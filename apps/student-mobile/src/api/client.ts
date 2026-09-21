import axios, { AxiosInstance, AxiosError } from "axios";
import { getApiBaseUrl } from "./config";
import { getAuthToken } from "../utils/storage";

let onUnauthorizedCallback: (() => void) | null = null;

export function setUnauthorizedHandler(callback: () => void) {
  onUnauthorizedCallback = callback;
}

export const apiClient: AxiosInstance = axios.create({
  timeout: 20000,
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

// Response Interceptor for Error Formatting and 401 Session Expiry
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<any>) => {
    if (error.response?.status === 401) {
      if (onUnauthorizedCallback) {
        onUnauthorizedCallback();
      }
    }

    // Normalize FastAPI validation errors or error detail
    let message = error.message;
    if (error.response?.data) {
      const data = error.response.data;
      if (typeof data.detail === "string") {
        message = data.detail;
      } else if (Array.isArray(data.detail)) {
        message = data.detail.map((err: any) => `${err.loc?.slice(-1)[0] || "Field"}: ${err.msg}`).join(", ");
      } else if (typeof data.message === "string") {
        message = data.message;
      }
    } else if (error.code === "ECONNABORTED" || !error.response) {
      message = `Cannot connect to ProofPath server at ${getApiBaseUrl()}. Please verify the backend is running.`;
    }

    const enhancedError = new Error(message);
    (enhancedError as any).status = error.response?.status;
    (enhancedError as any).originalError = error;
    return Promise.reject(enhancedError);
  }
);
