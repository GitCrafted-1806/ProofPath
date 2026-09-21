import { apiClient } from "./client";
import {
  StudentProfileResponse,
  StudentProfileUpdateRequest,
  PublicStudentProfileResponse,
} from "../types";

export async function fetchStudentProfile(): Promise<StudentProfileResponse> {
  const response = await apiClient.get<StudentProfileResponse>("/api/v1/students/me");
  return response.data;
}

export async function updateStudentProfile(
  payload: StudentProfileUpdateRequest
): Promise<StudentProfileResponse> {
  const response = await apiClient.patch<StudentProfileResponse>("/api/v1/students/me", payload);
  return response.data;
}

export async function fetchPublicStudentProfile(
  publicProfileId: string
): Promise<PublicStudentProfileResponse> {
  const response = await apiClient.get<PublicStudentProfileResponse>(
    `/api/v1/students/public/${publicProfileId}`
  );
  return response.data;
}
