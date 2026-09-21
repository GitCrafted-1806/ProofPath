"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import NextLink from "next/link";
import {
  api,
  formatApiError,
  StudentProfileDetail,
  EvidenceItem,
  AssessmentItem,
  SkillVerificationStatus,
  AuthenticityState,
} from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { ErrorState, LoadingState, EmptyState } from "@/components/StatusFeedback";
import {
  ArrowLeft,
  GraduationCap,
  Award,
  FileText,
  GitBranch,
  CheckCircle,
  AlertTriangle,
  Send,
  Loader2,
  ExternalLink,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Clock,
  Building,
} from "lucide-react";

export default function StudentProfilePage() {
  const params = useParams();
  const router = useRouter();
  const studentId = params.id as string;
  const { token } = useAuth();

  const [student, setStudent] = useState<StudentProfileDetail | null>(null);
  const [evidenceList, setEvidenceList] = useState<EvidenceItem[]>([]);
  const [assessments, setAssessments] = useState<AssessmentItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Request Assessment Modal State
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [modalSkillId, setModalSkillId] = useState<string>("");
  const [modalType, setModalType] = useState<string>("PRACTICAL");
  const [isSubmittingAssessment, setIsSubmittingAssessment] = useState<boolean>(false);
  const [modalMessage, setModalMessage] = useState<{ type: "success" | "error"; text: string } | null>(
    null
  );

  // Verification Action State
  const [verifyingEvidenceId, setVerifyingEvidenceId] = useState<string | null>(null);
  const [verificationFeedback, setVerificationFeedback] = useState<string | null>(null);

  const fetchStudentDossier = useCallback(async () => {
    if (!token || !studentId) return;
    setIsLoading(true);
    setError(null);

    try {
      const [studentRes, evidenceRes, assessmentsRes] = await Promise.all([
        api.get<StudentProfileDetail>(`/api/v1/students/${studentId}`),
        api.get<EvidenceItem[]>(`/api/v1/evidence/student/${studentId}`),
        api.get<AssessmentItem[]>(`/api/v1/assessments/student/${studentId}`),
      ]);

      setStudent(studentRes.data);
      setEvidenceList(evidenceRes.data);
      setAssessments(assessmentsRes.data);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setIsLoading(false);
    }
  }, [token, studentId]);

  useEffect(() => {
    fetchStudentDossier();
  }, [fetchStudentDossier]);

  // Institutional Verification Handler (Preserves Phase 2 RBAC)
  const handleVerifyEvidence = async (evidenceId: string) => {
    setVerifyingEvidenceId(evidenceId);
    setVerificationFeedback(null);
    try {
      await api.patch(`/api/v1/evidence/${evidenceId}/verify`, {
        authenticity_state: "INSTITUTION_VERIFIED",
        remarks: "Verified by Placement Coordinator during dossier audit",
      });
      setVerificationFeedback("Evidence authenticity verified and logged in audit trail.");
      // Refresh dossier
      await fetchStudentDossier();
    } catch (err) {
      setVerificationFeedback(`Verification failed: ${formatApiError(err)}`);
    } finally {
      setVerifyingEvidenceId(null);
    }
  };

  // Request Assessment Handler
  const handleRequestAssessment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!modalSkillId) return;
    setIsSubmittingAssessment(true);
    setModalMessage(null);

    try {
      const res = await api.post("/api/v1/assessments/request", {
        student_id: studentId,
        skill_id: modalSkillId,
        type: modalType,
      });

      setModalMessage({
        type: "success",
        text: res.data.message || "Assessment request dispatched successfully.",
      });
      // Refresh dossier
      await fetchStudentDossier();
      setTimeout(() => {
        setIsModalOpen(false);
        setModalMessage(null);
      }, 1800);
    } catch (err) {
      setModalMessage({
        type: "error",
        text: formatApiError(err),
      });
    } finally {
      setIsSubmittingAssessment(false);
    }
  };

  if (isLoading) {
    return <LoadingState message="Loading student academic dossier & verification telemetry..." />;
  }

  if (error || !student) {
    return (
      <div className="space-y-4">
        <NextLink
          href="/students"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Student Directory</span>
        </NextLink>
        <ErrorState
          title="Dossier Not Found"
          message={error || "Student profile could not be loaded."}
          onRetry={fetchStudentDossier}
        />
      </div>
    );
  }

  const getStatusBadge = (status: SkillVerificationStatus) => {
    switch (status) {
      case "SKILL_VERIFIED":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "SKILL_ASSESSED":
        return "bg-cyan-500/10 text-cyan-400 border-cyan-500/20";
      case "EVIDENCE_SUPPORTED":
        return "bg-amber-500/10 text-amber-400 border-amber-500/20";
      default:
        return "bg-slate-800 text-slate-400 border-slate-700";
    }
  };

  const documentEvidence = evidenceList.filter((e) => e.type !== "GITHUB_REPO");
  const githubEvidence = evidenceList.filter((e) => e.type === "GITHUB_REPO");

  return (
    <div className="space-y-8">
      {/* Navigation */}
      <div>
        <NextLink
          href="/students"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Student Directory</span>
        </NextLink>
      </div>

      {/* Verification Feedback Banner */}
      {verificationFeedback && (
        <div className="rounded-lg border border-indigo-500/30 bg-indigo-500/10 p-3.5 flex items-center justify-between text-xs text-indigo-300">
          <span>{verificationFeedback}</span>
          <button
            onClick={() => setVerificationFeedback(null)}
            className="text-slate-400 hover:text-white font-bold ml-2"
          >
            ✕
          </button>
        </div>
      )}

      {/* Student Dossier Header Card */}
      <div className="bg-[#131926] border border-[#1F293D] rounded-2xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight text-white">{student.full_name}</h1>
              <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-xs font-medium text-indigo-300">
                {student.qualification} • {student.branch}
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-1">{student.email}</p>
            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 mt-3">
              <span className="flex items-center gap-1.5">
                <Building className="w-3.5 h-3.5 text-slate-500" />
                {student.college_name}
              </span>
              <span>•</span>
              <span>Graduation: Class of {student.academic_year}</span>
              <span>•</span>
              <span className="font-semibold text-white">CGPA: {student.cgpa.toFixed(2)}</span>
            </div>
          </div>

          {/* Action: Request Assessment */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                if (student.skills.length > 0) {
                  setModalSkillId(student.skills[0].skill_id);
                }
                setIsModalOpen(true);
              }}
              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-indigo-600/20 transition-all cursor-pointer"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Request Skill Assessment</span>
            </button>
          </div>
        </div>
      </div>

      {/* Section 1: Deterministic Skills Verification Status */}
      <div className="bg-[#131926] border border-[#1F293D] rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-white">Skill Verification Matrix</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Determined strictly via deterministic evidence + assessment criteria
            </p>
          </div>
        </div>

        {student.skills.length === 0 ? (
          <p className="text-xs text-slate-500 italic py-4">No skills mapped for this candidate.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {student.skills.map((s) => (
              <div
                key={s.skill_id}
                className="bg-[#0B0F17] border border-[#1F293D] rounded-lg p-4 flex flex-col justify-between"
              >
                <div>
                  <div className="text-sm font-semibold text-white">{s.skill_name}</div>
                  <div className="mt-2">
                    <span
                      className={`inline-block px-2.5 py-1 rounded text-[11px] font-medium border ${getStatusBadge(
                        s.verification_status
                      )}`}
                    >
                      {s.verification_status}
                    </span>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-[#1F293D]/60 flex items-center justify-between">
                  <span className="text-[10px] text-slate-500">
                    Updated {new Date(s.updated_at).toLocaleDateString()}
                  </span>
                  <button
                    onClick={() => {
                      setModalSkillId(s.skill_id);
                      setIsModalOpen(true);
                    }}
                    className="text-[11px] font-medium text-indigo-400 hover:text-indigo-300"
                  >
                    Test
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Section 2: Document Evidence & Institutional Verification */}
      <div className="bg-[#131926] border border-[#1F293D] rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-white">Document Evidence & Certificates</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Inspected certificates and project documentation uploaded by student
            </p>
          </div>
          <span className="text-xs text-slate-400 font-mono">{documentEvidence.length} files</span>
        </div>

        {documentEvidence.length === 0 ? (
          <p className="text-xs text-slate-500 italic py-4">No document evidence uploaded yet.</p>
        ) : (
          <div className="divide-y divide-[#1F293D]">
            {documentEvidence.map((ev) => {
              const meta = ev.extracted_metadata || {};
              const isVerified = ev.authenticity_state === "INSTITUTION_VERIFIED";

              return (
                <div key={ev.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-indigo-400" />
                      <span className="text-sm font-medium text-white">{ev.original_filename}</span>
                      <span
                        className={`text-[10px] font-medium px-2 py-0.5 rounded border ${
                          isVerified
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                            : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                        }`}
                      >
                        {ev.authenticity_state}
                      </span>
                    </div>

                    <div className="text-xs text-slate-400 flex flex-wrap gap-x-4 gap-y-1 pt-1">
                      {meta.issuer && <span>Issuer: <strong className="text-slate-300">{meta.issuer}</strong></span>}
                      {meta.issue_date && <span>Date: <strong className="text-slate-300">{meta.issue_date}</strong></span>}
                      {meta.sha256 && (
                        <span className="font-mono text-[10px] text-slate-500 truncate max-w-xs">
                          SHA: {meta.sha256.substring(0, 16)}...
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-1.5 pt-1">
                      <span className="text-[10px] text-slate-500">Mapped Skills:</span>
                      {ev.mapped_skills.map((sk) => (
                        <span key={sk} className="text-[10px] px-1.5 py-0.5 rounded bg-[#0B0F17] text-slate-300 border border-[#1F293D]">
                          {sk}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Institution Verification Action (Preserving Phase 2 authorization) */}
                  <div className="sm:text-right shrink-0">
                    {isVerified ? (
                      <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-medium">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Institution Verified</span>
                      </div>
                    ) : (
                      <button
                        onClick={() => handleVerifyEvidence(ev.id)}
                        disabled={verifyingEvidenceId === ev.id}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 text-xs font-semibold transition-colors cursor-pointer"
                      >
                        {verifyingEvidenceId === ev.id ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <ShieldCheck className="w-3.5 h-3.5" />
                        )}
                        <span>Institution Verify</span>
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Section 3: GitHub Evidence */}
      <div className="bg-[#131926] border border-[#1F293D] rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-white">GitHub Project Evidence</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Verified software code repositories linked by candidate
            </p>
          </div>
          <span className="text-xs text-slate-400 font-mono">{githubEvidence.length} repos</span>
        </div>

        {githubEvidence.length === 0 ? (
          <p className="text-xs text-slate-500 italic py-4">No GitHub repositories connected yet.</p>
        ) : (
          <div className="divide-y divide-[#1F293D]">
            {githubEvidence.map((gh) => (
              <div key={gh.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <GitBranch className="w-4 h-4 text-white" />
                    <span className="text-sm font-medium text-white">{gh.original_filename}</span>
                  </div>
                  <div className="flex items-center gap-1.5 pt-2">
                    <span className="text-[10px] text-slate-500">Extracted Skills:</span>
                    {gh.mapped_skills.map((sk) => (
                      <span key={sk} className="text-[10px] px-1.5 py-0.5 rounded bg-[#0B0F17] text-slate-300 border border-[#1F293D]">
                        {sk}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="text-right">
                  <span className="text-xs font-medium text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded border border-emerald-500/20">
                    Project Verified
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Section 4: Assessment History */}
      <div className="bg-[#131926] border border-[#1F293D] rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-white">Assessment Execution History</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Proctored question evaluations, scores, and status transitions
            </p>
          </div>
          <span className="text-xs text-slate-400 font-mono">{assessments.length} sessions</span>
        </div>

        {assessments.length === 0 ? (
          <p className="text-xs text-slate-500 italic py-4">No assessments taken by candidate yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-[#0B0F17] text-slate-400 uppercase tracking-wider text-[11px] border-b border-[#1F293D]">
                <tr>
                  <th className="py-2.5 px-3">Skill</th>
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Score</th>
                  <th className="py-2.5 px-3">Result</th>
                  <th className="py-2.5 px-3">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1F293D]">
                {assessments.map((a) => (
                  <tr key={a.id} className="hover:bg-[#182030]/50">
                    <td className="py-3 px-3 font-medium text-white">{a.skill_name}</td>
                    <td className="py-3 px-3">
                      <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                        {a.type}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="font-mono text-[11px]">{a.status}</span>
                    </td>
                    <td className="py-3 px-3">
                      {a.score !== undefined ? `${a.score.toFixed(0)}%` : "N/A"}
                    </td>
                    <td className="py-3 px-3">
                      {a.passed === true ? (
                        <span className="text-emerald-400 font-medium flex items-center gap-1">
                          <CheckCircle className="w-3.5 h-3.5" />
                          PASSED
                        </span>
                      ) : a.passed === false ? (
                        <span className="text-rose-400 font-medium flex items-center gap-1">
                          <XCircle className="w-3.5 h-3.5" />
                          FAILED
                        </span>
                      ) : (
                        <span className="text-amber-400 font-medium flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5" />
                          PENDING
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-slate-500">
                      {new Date(a.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Request Assessment Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-[#131926] border border-[#1F293D] rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-base font-bold text-white mb-1">Request Skill Assessment</h3>
            <p className="text-xs text-slate-400 mb-4">
              Dispatch an assessment assignment to <strong className="text-slate-200">{student.full_name}</strong>.
            </p>

            {modalMessage && (
              <div
                className={`mb-4 rounded-lg p-3 text-xs flex items-start gap-2 ${
                  modalMessage.type === "success"
                    ? "bg-emerald-500/10 text-emerald-300 border border-emerald-500/30"
                    : "bg-rose-500/10 text-rose-300 border border-rose-500/30"
                }`}
              >
                {modalMessage.type === "success" ? (
                  <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400 mt-0.5" />
                ) : (
                  <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
                )}
                <div className="leading-relaxed">{modalMessage.text}</div>
              </div>
            )}

            <form onSubmit={handleRequestAssessment} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Select Skill</label>
                <select
                  value={modalSkillId}
                  onChange={(e) => setModalSkillId(e.target.value)}
                  required
                  className="w-full px-3 py-2 bg-[#0B0F17] border border-[#1F293D] rounded-lg text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  {student.skills.map((s) => (
                    <option key={s.skill_id} value={s.skill_id}>
                      {s.skill_name} (Current: {s.verification_status})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Assessment Type</label>
                <select
                  value={modalType}
                  onChange={(e) => setModalType(e.target.value)}
                  required
                  className="w-full px-3 py-2 bg-[#0B0F17] border border-[#1F293D] rounded-lg text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="PRACTICAL">PRACTICAL (Coding & Problem Solving)</option>
                  <option value="FOLLOW_UP">FOLLOW_UP (Architecture & Advanced)</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg bg-[#1B2336] text-slate-300 hover:text-white text-xs font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingAssessment}
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer disabled:opacity-50"
                >
                  {isSubmittingAssessment ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Dispatching...</span>
                    </>
                  ) : (
                    <>
                      <Send className="w-3.5 h-3.5" />
                      <span>Assign Assessment</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
