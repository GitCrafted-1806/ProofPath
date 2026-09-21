import axios, { AxiosError } from "axios";

export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL?.trim() || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 60000,
});

// Request interceptor to attach JWT
api.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("proofpath_coordinator_token");
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for unified error formatting
export function formatApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const err = error as AxiosError<{ detail?: string | Array<{ msg: string }> }>;
    if (err.response?.data?.detail) {
      if (typeof err.response.data.detail === "string") {
        return err.response.data.detail;
      }
      if (Array.isArray(err.response.data.detail)) {
        return err.response.data.detail.map((d) => d.msg).join(", ");
      }
    }
    if (err.code === "ECONNABORTED") {
      return "Connection timed out. The backend server might be starting up (Render free-tier cold start can take up to 60s). Please try again.";
    }
    if (err.code === "ERR_NETWORK" || !err.response) {
      return `Cannot connect to ProofPath API server (${API_BASE_URL}). Please ensure the backend is running and CORS is permitted.`;
    }
    if (err.response?.status === 401) {
      return "Session expired or invalid credentials. Please log in again.";
    }
    if (err.response?.status === 403) {
      return "Access denied: Placement coordinator privileges required.";
    }
    return `Server error (${err.response?.status}): ${err.message}`;
  }
  return (error as Error)?.message || "An unexpected error occurred.";
}

// Data Types
export type SkillVerificationStatus =
  | "UNVERIFIED"
  | "EVIDENCE_SUPPORTED"
  | "SKILL_ASSESSED"
  | "SKILL_VERIFIED";

export type AuthenticityState =
  | "SUBMITTED"
  | "SOURCE_SUPPORTED"
  | "INSTITUTION_VERIFIED"
  | "REJECTED";

export interface User {
  id: string;
  email: string;
  role: "STUDENT" | "PLACEMENT_COORDINATOR";
}

export interface StudentSkill {
  skill_id: string;
  skill_name: string;
  verification_status: SkillVerificationStatus;
  updated_at: string;
}

export interface StudentDirectoryItem {
  id: string;
  user_id: string;
  email: string;
  full_name: string;
  qualification: string;
  college_name: string;
  branch: string;
  academic_year: number;
  cgpa: number;
  public_profile_id: string;
  is_public: boolean;
  skills_count: number;
  verified_skills_count: number;
  skills: StudentSkill[];
}

export interface StudentDirectoryListResponse {
  total: number;
  students: StudentDirectoryItem[];
}

export interface StudentProfileDetail {
  id: string;
  user_id: string;
  email: string;
  full_name: string;
  qualification: string;
  college_name: string;
  branch: string;
  academic_year: number;
  cgpa: number;
  public_profile_id: string;
  is_public: boolean;
  skills: StudentSkill[];
}

export interface EvidenceItem {
  id: string;
  student_id: string;
  type: "CERTIFICATE" | "PROJECT_DOCUMENT" | "GITHUB_REPO";
  original_filename: string;
  authenticity_state: AuthenticityState;
  extracted_metadata?: Record<string, any>;
  mapped_skills: string[];
  created_at: string;
}

export interface AssessmentItem {
  id: string;
  skill_id: string;
  skill_name: string;
  type: "PRACTICAL" | "FOLLOW_UP";
  status: "PENDING" | "COMPLETED" | "FAILED";
  score?: number;
  passed?: boolean;
  evaluation_summary?: string;
  created_at: string;
  completed_at?: string;
}

export interface PlacementRequirement {
  id: string;
  coordinator_id: string;
  company_name: string;
  role_title: string;
  min_cgpa: number;
  eligible_branches: string[];
  required_skills: Record<string, string>;
  created_at: string;
}

export interface PlacementRequirementCreate {
  company_name: string;
  role_title: string;
  min_cgpa: number;
  eligible_branches: string[];
  required_skills: Record<string, string>;
}

export interface CandidateMatchItem {
  student_id: string;
  full_name: string;
  email: string;
  college_name?: string;
  branch: string;
  academic_year?: number;
  cgpa: number;
  is_matched: boolean;
  criteria_results: {
    cgpa: { required: number; actual: number; passed: boolean };
    branch: { eligible: string[]; actual: string; passed: boolean };
    skills: Record<string, { required: string; actual: string; passed: boolean }>;
  };
  failure_reasons: string[];
  skills: Record<string, string>;
}

export interface PlacementMatchResponse {
  requirement: PlacementRequirement;
  total_candidates: number;
  matched_count: number;
  unmatched_count: number;
  matches: CandidateMatchItem[];
}
