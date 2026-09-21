import { Platform } from "react-native";

/**
 * Dynamic resolution of ProofPath FastAPI backend URL
 */
function getDefaultBaseUrl(): string {
  // Check for explicitly configured environment variable
  if (process.env.EXPO_PUBLIC_API_URL) {
    return process.env.EXPO_PUBLIC_API_URL;
  }

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

let activeBaseUrl = getDefaultBaseUrl();

export function getApiBaseUrl(): string {
  return activeBaseUrl;
}

export function setApiBaseUrl(url: string): void {
  activeBaseUrl = url.trim().replace(/\/+$/, "");
}
