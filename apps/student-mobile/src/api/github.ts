import { apiClient } from "./client";
import {
  GitHubConnectionStatusResponse,
  GitHubOAuthStartResponse,
  GitHubRepositoryResponse,
  EvidenceResponse,
} from "../types";

export async function fetchGitHubStatus(): Promise<GitHubConnectionStatusResponse> {
  const response = await apiClient.get<GitHubConnectionStatusResponse>("/api/v1/github/status");
  return response.data;
}

export async function startGitHubOAuth(): Promise<GitHubOAuthStartResponse> {
  const response = await apiClient.get<GitHubOAuthStartResponse>("/api/v1/github/oauth/start");
  return response.data;
}

export async function completeGitHubCallback(code: string, state: string): Promise<void> {
  await apiClient.get(`/api/v1/github/callback`, {
    params: { code, state },
  });
}

export async function connectDemoGitHub(): Promise<void> {
  // In DEMO_MODE, initiate OAuth state and immediately invoke the callback
  const start = await startGitHubOAuth();
  await completeGitHubCallback("demo_oauth_code", start.state);
}

export async function fetchGitHubRepositories(): Promise<GitHubRepositoryResponse[]> {
  const response = await apiClient.get<GitHubRepositoryResponse[]>("/api/v1/github/repositories");
  return response.data;
}

export async function selectGitHubRepository(repoFullName: string): Promise<EvidenceResponse> {
  const response = await apiClient.post<EvidenceResponse>("/api/v1/github/repositories/select", {
    repo_full_name: repoFullName,
  });
  return response.data;
}

export async function fetchGitHubEvidence(): Promise<EvidenceResponse[]> {
  const response = await apiClient.get<EvidenceResponse[]>("/api/v1/github/evidence");
  return response.data;
}

export async function disconnectGitHub(): Promise<{ message: string }> {
  const response = await apiClient.post<{ message: string }>("/api/v1/github/disconnect");
  return response.data;
}
