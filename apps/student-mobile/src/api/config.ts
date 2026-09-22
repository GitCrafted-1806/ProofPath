import { Platform } from "react-native";

export const PRODUCTION_API_URL = "https://proofpath-api-cybc.onrender.com";

/**
 * Dynamic resolution of ProofPath FastAPI backend URL
 */
function getDefaultBaseUrl(): string {
  // a. If EXPO_PUBLIC_API_URL is explicitly provided, use it
  if (process.env.EXPO_PUBLIC_API_URL && process.env.EXPO_PUBLIC_API_URL.trim()) {
    return process.env.EXPO_PUBLIC_API_URL.trim().replace(/\/+$/, "");
  }

  // b. If __DEV__ is true and no EXPO_PUBLIC_API_URL is provided:
  const isDev = typeof __DEV__ !== "undefined" ? __DEV__ : process.env.NODE_ENV !== "production";

  if (isDev) {
    // Web and iOS simulator can connect directly to localhost
    if (Platform.OS === "web" || Platform.OS === "ios") {
      return "http://127.0.0.1:8000";
    }

    // Android emulator loops back to host via 10.0.2.2
    if (Platform.OS === "android") {
      return "http://10.0.2.2:8000";
    }

    return "http://127.0.0.1:8000";
  }

  // c. If __DEV__ is false and no EXPO_PUBLIC_API_URL is provided:
  return PRODUCTION_API_URL;
}

let activeBaseUrl = getDefaultBaseUrl();

export function getApiBaseUrl(): string {
  return activeBaseUrl;
}

export function setApiBaseUrl(url: string): void {
  activeBaseUrl = url.trim().replace(/\/+$/, "");
}
