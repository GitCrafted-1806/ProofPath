import { apiClient } from "./client";
import { TokenResponse, UserResponse } from "../types";

export async function loginStudent(email: string, password: string): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/api/v1/auth/login", {
    email: email.trim(),
    password,
  });
  return response.data;
}

export async function registerStudent(payload: {
  email: string;
  password: string;
  full_name: string;
  college_name?: string;
  branch?: string;
  academic_year?: number;
  cgpa?: number;
  qualification?: string;
  skills?: string[];
}): Promise<UserResponse> {
  const response = await apiClient.post<UserResponse>("/api/v1/auth/register", {
    ...payload,
    email: payload.email.trim(),
    role: "STUDENT",
  });
  return response.data;
}

export async function getCurrentUser(): Promise<UserResponse> {
  const response = await apiClient.get<UserResponse>("/api/v1/auth/me");
  return response.data;
}
