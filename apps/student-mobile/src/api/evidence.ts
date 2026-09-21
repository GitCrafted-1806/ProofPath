import { apiClient } from "./client";
import { EvidenceResponse, EvidenceType } from "../types";
import { Platform } from "react-native";

export async function fetchMyEvidence(): Promise<EvidenceResponse[]> {
  const response = await apiClient.get<EvidenceResponse[]>("/api/v1/evidence/me");
  return response.data;
}

export async function fetchEvidenceDetail(evidenceId: string): Promise<EvidenceResponse> {
  const response = await apiClient.get<EvidenceResponse>(`/api/v1/evidence/${evidenceId}`);
  return response.data;
}

export interface UploadEvidenceParams {
  uri: string;
  name: string;
  mimeType: string;
  type: "CERTIFICATE" | "PROJECT_DOCUMENT";
  webFile?: any;
}

export async function uploadEvidence(params: UploadEvidenceParams): Promise<EvidenceResponse> {
  const formData = new FormData();

  if (Platform.OS === "web" && params.webFile) {
    formData.append("file", params.webFile);
  } else if (Platform.OS === "web" && params.uri.startsWith("blob:")) {
    // Convert blob url to Blob for Web
    const blob = await fetch(params.uri).then((r) => r.blob());
    formData.append("file", blob, params.name);
  } else {
    // Native (iOS/Android)
    formData.append("file", {
      uri: params.uri,
      name: params.name,
      type: params.mimeType || "application/pdf",
    } as any);
  }

  formData.append("type", params.type);

  const response = await apiClient.post<EvidenceResponse>("/api/v1/evidence/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    timeout: 30000,
  });

  return response.data;
}

export async function deleteEvidence(evidenceId: string): Promise<{ message: string }> {
  const response = await apiClient.delete<{ message: string }>(`/api/v1/evidence/${evidenceId}`);
  return response.data;
}
