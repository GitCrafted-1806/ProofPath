import { apiClient } from "./client";
import {
  SkillAssessmentAvailabilityResponse,
  AssessmentTakeResponse,
  AssessmentResultResponse,
  AssessmentHistoryItemResponse,
} from "../types";

export async function fetchAvailableAssessments(): Promise<SkillAssessmentAvailabilityResponse[]> {
  const response = await apiClient.get<SkillAssessmentAvailabilityResponse[]>(
    "/api/v1/assessments/available"
  );
  return response.data;
}

export async function startAssessment(
  skillId: string,
  type: "PRACTICAL" | "FOLLOW_UP"
): Promise<AssessmentTakeResponse> {
  const response = await apiClient.post<AssessmentTakeResponse>("/api/v1/assessments/start", {
    skill_id: skillId,
    type,
  });
  return response.data;
}

export async function fetchAssessmentDetails(
  assessmentId: string
): Promise<AssessmentTakeResponse | AssessmentResultResponse> {
  const response = await apiClient.get<AssessmentTakeResponse | AssessmentResultResponse>(
    `/api/v1/assessments/${assessmentId}`
  );
  return response.data;
}

export async function submitAssessment(
  assessmentId: string,
  answers: Record<string, any>
): Promise<AssessmentResultResponse> {
  const response = await apiClient.post<AssessmentResultResponse>(
    `/api/v1/assessments/${assessmentId}/submit`,
    { answers }
  );
  return response.data;
}

export async function fetchAssessmentHistory(): Promise<AssessmentHistoryItemResponse[]> {
  const response = await apiClient.get<AssessmentHistoryItemResponse[]>("/api/v1/assessments/history");
  return response.data;
}
