/**
 * TypeScript interface definitions strictly aligned with FastAPI backend schemas.
 */

export type UserRole = "STUDENT" | "PLACEMENT_COORDINATOR";

export type SkillVerificationStatus =
  | "UNVERIFIED"
  | "EVIDENCE_SUPPORTED"
  | "SKILL_ASSESSED"
  | "SKILL_VERIFIED";

export type EvidenceType = "CERTIFICATE" | "PROJECT_DOCUMENT" | "GITHUB_REPO";

export type AuthenticityState =
  | "SUBMITTED"
  | "SOURCE_SUPPORTED"
  | "INSTITUTION_VERIFIED"
  | "REJECTED";

export interface UserResponse {
  id: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  role: UserRole;
  user_id: string;
}

export interface StudentSkillResponse {
  skill_id: string;
  skill_name: string;
  verification_status: SkillVerificationStatus;
  updated_at: string;
}

export interface StudentProfileResponse {
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
  skills: StudentSkillResponse[];
}

export interface StudentProfileUpdateRequest {
  full_name?: string;
  qualification?: string;
  college_name?: string;
  branch?: string;
  academic_year?: number;
  cgpa?: number;
  is_public?: boolean;
}

export interface PublicStudentProfileResponse {
  id: string;
  full_name: string;
  qualification: string;
  college_name: string;
  branch: string;
  academic_year: number;
  cgpa: number;
  public_profile_id: string;
  is_public: boolean;
  skills: StudentSkillResponse[];
}

export interface EvidenceResponse {
  id: string;
  student_id: string;
  type: EvidenceType;
  file_path: string;
  original_filename: string | null;
  authenticity_state: AuthenticityState;
  extracted_metadata: Record<string, any>;
  mapped_skills: string[];
  created_at: string;
  updated_at?: string;
}

export interface GitHubConnectionStatusResponse {
  is_connected: boolean;
  github_username: string | null;
  avatar_url: string | null;
  profile_url: string | null;
  connected_at: string | null;
}

export interface GitHubOAuthStartResponse {
  authorize_url: string;
  state: string;
}

export interface GitHubRepositoryResponse {
  name: string;
  full_name: string;
  owner: string;
  description: string | null;
  html_url: string;
  default_branch: string;
  language: string | null;
  stars: number;
  forks: number;
  is_private: boolean;
  topics: string[];
  updated_at?: string | null;
}

export interface GitHubRepoSelectRequest {
  repo_full_name: string;
}

export interface SkillAssessmentAvailabilityResponse {
  skill_id: string;
  skill_name: string;
  current_status: SkillVerificationStatus;
  practical_available: boolean;
  followup_available: boolean;
  pending_assessment_id: string | null;
  reason: string | null;
}

export type QuestionType = "MULTIPLE_CHOICE" | "NUMERICAL_INPUT" | "CODE_OUTPUT";

export interface AssessmentQuestionClient {
  id: string;
  question: string;
  type: QuestionType;
  options?: string[] | null;
  code_snippet?: string | null;
  points: number;
}

export interface AssessmentStartRequest {
  skill_id: string;
  type: "PRACTICAL" | "FOLLOW_UP";
}

export interface AssessmentTakeResponse {
  id: string;
  student_id: string;
  skill_id: string;
  skill_name: string;
  type: "PRACTICAL" | "FOLLOW_UP";
  status: "PENDING" | "COMPLETED" | "FAILED";
  questions: AssessmentQuestionClient[];
  created_at: string;
}

export interface QuestionResultFeedback {
  question_id: string;
  question: string;
  submitted_answer: any;
  correct_answer: any;
  is_correct: boolean;
  explanation: string | null;
}

export interface AssessmentResultResponse {
  id: string;
  student_id: string;
  skill_id: string;
  skill_name: string;
  type: "PRACTICAL" | "FOLLOW_UP";
  status: "COMPLETED" | "FAILED";
  score: number;
  passed: boolean;
  evaluation_summary: string;
  completed_at: string;
  feedback: QuestionResultFeedback[];
  new_skill_status: SkillVerificationStatus;
}

export interface AssessmentHistoryItemResponse {
  id: string;
  skill_id: string;
  skill_name: string;
  type: string;
  status: string;
  score: number | null;
  passed: boolean;
  evaluation_summary: string | null;
  created_at: string;
  completed_at: string | null;
}
