import * as SecureStore from "expo-secure-store";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { Platform } from "react-native";

const TOKEN_KEY = "proofpath_access_token";
const USER_KEY = "proofpath_user_id";

let memoryFallback: Record<string, string> = {};

export async function saveSecureItem(key: string, value: string): Promise<void> {
  memoryFallback[key] = value;
  try {
    if (Platform.OS === "web") {
      await AsyncStorage.setItem(key, value);
    } else {
      await SecureStore.setItemAsync(key, value);
    }
  } catch (error) {
    try {
      await AsyncStorage.setItem(key, value);
    } catch {
      // preserved in memoryFallback
    }
  }
}

export async function getSecureItem(key: string): Promise<string | null> {
  try {
    if (Platform.OS === "web") {
      const val = await AsyncStorage.getItem(key);
      if (val !== null) return val;
      return memoryFallback[key] || null;
    }
    const val = await SecureStore.getItemAsync(key);
    if (val !== null) return val;
    const asyncVal = await AsyncStorage.getItem(key);
    if (asyncVal !== null) return asyncVal;
    return memoryFallback[key] || null;
  } catch (error) {
    try {
      const asyncVal = await AsyncStorage.getItem(key);
      if (asyncVal !== null) return asyncVal;
      return memoryFallback[key] || null;
    } catch {
      return memoryFallback[key] || null;
    }
  }
}

export async function deleteSecureItem(key: string): Promise<void> {
  delete memoryFallback[key];
  try {
    if (Platform.OS !== "web") {
      await SecureStore.deleteItemAsync(key);
    }
  } catch {
    // Ignore SecureStore delete error
  }
  try {
    await AsyncStorage.removeItem(key);
  } catch {
    // Ignore AsyncStorage delete error
  }
}

export async function saveAuthToken(token: string, userId?: string): Promise<void> {
  await saveSecureItem(TOKEN_KEY, token);
  if (userId) {
    await saveSecureItem(USER_KEY, userId);
  }
}

export async function getAuthToken(): Promise<string | null> {
  return await getSecureItem(TOKEN_KEY);
}

export async function clearAuthSession(): Promise<void> {
  await deleteSecureItem(TOKEN_KEY);
  await deleteSecureItem(USER_KEY);
  delete memoryFallback[TOKEN_KEY];
  delete memoryFallback[USER_KEY];
}

