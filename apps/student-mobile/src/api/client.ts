import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from "axios";
import { getApiBaseUrl } from "./config";
import { getAuthToken } from "../utils/storage";

let onUnauthorizedCallback: (() => void) | null = null;

export function setUnauthorizedHandler(callback: () => void) {
  onUnauthorizedCallback = callback;
}

// Timeout: 60 seconds to accommodate Render free-tier cold-start wakeups (~30-50s)
const DEFAULT_TIMEOUT_MS = 60000;
const MAX_RETRIES = 2;
const RETRY_DELAY_BASE_MS = 1500;

interface RetryConfig extends InternalAxiosRequestConfig {
  _retryCount?: number;
}

export const apiClient: AxiosInstance = axios.create({
  timeout: DEFAULT_TIMEOUT_MS,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

// Dynamic Base URL and Bearer Token Interceptor
apiClient.interceptors.request.use(
  async (config) => {
    config.baseURL = getApiBaseUrl();
    const token = await getAuthToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    } else {
      delete config.headers.Authorization;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

function isSafeToRetryRequest(config?: RetryConfig): boolean {
  if (!config) return false;
  const method = (config.method || "get").toUpperCase();
  // Safe idempotent read operations
  if (method === "GET" || method === "HEAD" || method === "OPTIONS") {
    return true;
  }
  // Explicitly safe auth/login request on cold-start (credential check only, no state mutation)
  const url = config.url || "";
  if (method === "POST" && url.includes("/auth/login")) {
    return true;
  }
  // Never retry arbitrary state-changing requests (evidence uploads, assessments, profile updates)
  return false;
}

function isRetryableError(error: AxiosError): boolean {
  // Do not retry cancelled requests
  if (axios.isCancel(error)) {
    return false;
  }

  // Network error (no response) or request timeout
  if (!error.response || error.code === "ECONNABORTED") {
    return true;
  }

  // Gateway errors often returned by Render proxy during container spin-up
  const status = error.response.status;
  return status === 502 || status === 503 || status === 504;
}

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// Response Interceptor for Error Formatting, Retries, and 401 Session Expiry
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<any>) => {
    const config = error.config as RetryConfig | undefined;

    // Retry transient network or cold-start gateway failures only for safe/idempotent requests
    if (config && isSafeToRetryRequest(config) && isRetryableError(error)) {
      const currentRetry = config._retryCount || 0;
      if (currentRetry < MAX_RETRIES) {
        config._retryCount = currentRetry + 1;
        const waitMs = RETRY_DELAY_BASE_MS * (currentRetry + 1);
        await delay(waitMs);
        return apiClient.request(config);
      }
    }

    if (error.response?.status === 401) {
      if (onUnauthorizedCallback) {
        onUnauthorizedCallback();
      }
    }

    // Normalize FastAPI validation errors or error detail
    let message = error.message;
    const isNetworkOrColdStart =
      error.code === "ECONNABORTED" ||
      !error.response ||
      (error.response?.status !== undefined && error.response.status >= 502 && error.response.status <= 504);

    if (error.response?.data) {
      const data = error.response.data;
      if (typeof data.detail === "string") {
        message = data.detail;
      } else if (Array.isArray(data.detail)) {
        message = data.detail.map((err: any) => `${err.loc?.slice(-1)[0] || "Field"}: ${err.msg}`).join(", ");
      } else if (typeof data.message === "string") {
        message = data.message;
      } else if (isNetworkOrColdStart) {
        message = `Cannot connect to ProofPath server at ${getApiBaseUrl()}. The backend may be waking from idle. Please try again shortly.`;
      }
    } else if (isNetworkOrColdStart) {
      message = `Cannot connect to ProofPath server at ${getApiBaseUrl()}. The backend may be waking from idle or unreachable. Please try again in a moment.`;
    }

    const enhancedError = new Error(message);
    (enhancedError as any).status = error.response?.status;
    (enhancedError as any).originalError = error;
    return Promise.reject(enhancedError);
  }
);
