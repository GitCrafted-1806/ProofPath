"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import NextLink from "next/link";
import {
  api,
  API_BASE_URL,
  formatApiError,
  PlacementMatchResponse,
  CandidateMatchItem,
} from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { ErrorState, LoadingState, EmptyState } from "@/components/StatusFeedback";
import {
  ArrowLeft,
  Download,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Filter,
  Users,
  ChevronRight,
  Loader2,
  Building,
  GraduationCap,
  Award,
} from "lucide-react";

export default function RequirementMatchPage() {
  const params = useParams();
  const reqId = params.id as string;
  const { token } = useAuth();

  const [matchData, setMatchData] = useState<PlacementMatchResponse | null>(null);
  const [activeTab, setActiveTab] = useState<"ALL" | "MATCHED" | "UNMATCHED">("ALL");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const runMatch = useCallback(async () => {
    if (!token || !reqId) return;
    setIsLoading(true);
    setError(null);

    try {
      const res = await api.post<PlacementMatchResponse>(
        `/api/v1/placements/requirements/${reqId}/match`
      );
      setMatchData(res.data);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setIsLoading(false);
    }
  }, [token, reqId]);

  useEffect(() => {
    runMatch();
  }, [runMatch]);

  const handleExportCsv = async () => {
    if (!token || !reqId) return;
    setIsExporting(true);
    try {
      const response = await api.get(`/api/v1/placements/requirements/${reqId}/export`, {
        responseType: "blob",
      });

      // Create download link
      const blob = new Blob([response.data], { type: "text/csv" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;

      const company = matchData?.requirement.company_name.replace(/\s+/g, "_") || "placement";
      const role = matchData?.requirement.role_title.replace(/\s+/g, "_") || "candidates";
      a.download = `${company}_${role}_results.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      alert(`Failed to export CSV: ${formatApiError(err)}`);
    } finally {
      setIsExporting(false);
    }
  };

  if (isLoading) {
    return <LoadingState message="Executing deterministic placement matching against database..." />;
  }

  if (error || !matchData) {
    return (
      <div className="space-y-4">
        <NextLink
          href="/requirements"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Requirements</span>
        </NextLink>
        <ErrorState
          title="Matching Execution Failed"
          message={error || "Could not execute deterministic candidate match."}
          onRetry={runMatch}
        />
      </div>
    );
  }

  const { requirement, total_candidates, matched_count, unmatched_count, matches } = matchData;

  const filteredMatches = matches.filter((m) => {
    if (activeTab === "MATCHED") return m.is_matched;
    if (activeTab === "UNMATCHED") return !m.is_matched;
    return true;
  });

  return (
    <div className="space-y-8">
      {/* Navigation */}
      <div>
        <NextLink
          href="/requirements"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Requirements</span>
        </NextLink>
      </div>

      {/* Requirement Criteria Summary Card */}
      <div className="bg-[#131926] border border-[#1F293D] rounded-2xl p-6 shadow-xl">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight text-white">
                {requirement.company_name}
              </h1>
              <span className="text-lg text-slate-400 font-medium">— {requirement.role_title}</span>
            </div>

            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 mt-3">
              <span className="flex items-center gap-1.5">
                <GraduationCap className="w-3.5 h-3.5 text-slate-500" />
                Min CGPA: <strong className="text-white">{requirement.min_cgpa.toFixed(2)}</strong>
              </span>
              <span>•</span>
              <span>
                Eligible Branches:{" "}
                <strong className="text-slate-200">
                  {requirement.eligible_branches.length > 0
                    ? requirement.eligible_branches.join(", ")
                    : "All"}
                </strong>
              </span>
              <span>•</span>
              <span>
                Required Skills:{" "}
                <strong className="text-slate-200">
                  {Object.entries(requirement.required_skills)
                    .map(([s, l]) => `${s} (${l.replace("SKILL_", "")})`)
                    .join(", ") || "None"}
                </strong>
              </span>
            </div>
          </div>

          {/* Secure CSV Export Button */}
          <div className="shrink-0">
            <button
              onClick={handleExportCsv}
              disabled={isExporting}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-600/20 transition-all cursor-pointer disabled:opacity-50"
            >
              {isExporting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Generating Secure CSV...</span>
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  <span>Export Placement Results (CSV)</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Counters & Filter Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2 bg-[#131926] border border-[#1F293D] rounded-xl p-1.5 text-xs font-medium">
          <button
            onClick={() => setActiveTab("ALL")}
            className={`px-3.5 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeTab === "ALL"
                ? "bg-[#1E293B] text-white border border-[#334155]"
                : "text-slate-400 hover:text-white"
            }`}
          >
            All Evaluated ({total_candidates})
          </button>
          <button
            onClick={() => setActiveTab("MATCHED")}
            className={`px-3.5 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeTab === "MATCHED"
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-semibold"
                : "text-slate-400 hover:text-emerald-400"
            }`}
          >
            Eligible Matches ({matched_count})
          </button>
          <button
            onClick={() => setActiveTab("UNMATCHED")}
            className={`px-3.5 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeTab === "UNMATCHED"
                ? "bg-rose-500/20 text-rose-300 border border-rose-500/30 font-semibold"
                : "text-slate-400 hover:text-rose-400"
            }`}
          >
            Unmatched ({unmatched_count})
          </button>
        </div>

        <div className="text-xs text-slate-500">
          Pure deterministic boolean compliance • Zero candidate ranking / AI scoring
        </div>
      </div>

      {/* Candidates Evaluation Table */}
      {filteredMatches.length === 0 ? (
        <EmptyState
          title="No Candidates in this Category"
          description="Adjust the filter tab above to view all candidates evaluated against this placement requirement."
        />
      ) : (
        <div className="bg-[#131926] border border-[#1F293D] rounded-xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-[#0B0F17] text-slate-400 uppercase tracking-wider text-[11px] border-b border-[#1F293D]">
                <tr>
                  <th className="py-3.5 px-4 font-semibold">Candidate</th>
                  <th className="py-3.5 px-4 font-semibold">Match Status</th>
                  <th className="py-3.5 px-4 font-semibold">CGPA</th>
                  <th className="py-3.5 px-4 font-semibold">Branch</th>
                  <th className="py-3.5 px-4 font-semibold">Required Skills Breakdown</th>
                  <th className="py-3.5 px-4 font-semibold">Unmet Criteria / Disqualification</th>
                  <th className="py-3.5 px-4 font-semibold text-right">Dossier</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1F293D]">
                {filteredMatches.map((candidate) => {
                  const cgpaRes = candidate.criteria_results.cgpa;
                  const branchRes = candidate.criteria_results.branch;
                  const skillsRes = candidate.criteria_results.skills || {};

                  return (
                    <tr
                      key={candidate.student_id}
                      className="hover:bg-[#182030]/60 transition-colors"
                    >
                      {/* Candidate */}
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-white text-sm">
                          {candidate.full_name}
                        </div>
                        <div className="text-slate-400 font-mono text-[11px]">
                          {candidate.email}
                        </div>
                      </td>

                      {/* Match Status */}
                      <td className="py-3.5 px-4">
                        {candidate.is_matched ? (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold text-[11px]">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            MATCHED
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800 text-slate-400 border border-slate-700 text-[11px]">
                            <XCircle className="w-3.5 h-3.5 text-slate-500" />
                            NOT MATCHED
                          </span>
                        )}
                      </td>

                      {/* CGPA */}
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-1.5">
                          {cgpaRes.passed ? (
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                          ) : (
                            <XCircle className="w-3.5 h-3.5 text-rose-400" />
                          )}
                          <span className="font-semibold text-white">
                            {candidate.cgpa.toFixed(2)}
                          </span>
                        </div>
                      </td>

                      {/* Branch */}
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-1.5">
                          {branchRes.passed ? (
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                          ) : (
                            <XCircle className="w-3.5 h-3.5 text-rose-400" />
                          )}
                          <span className="font-medium text-slate-200">{candidate.branch}</span>
                        </div>
                      </td>

                      {/* Skills Breakdown */}
                      <td className="py-3.5 px-4">
                        <div className="space-y-1">
                          {Object.keys(skillsRes).length === 0 ? (
                            <span className="text-slate-500 italic">No skills required</span>
                          ) : (
                            Object.entries(skillsRes).map(([sName, res]) => (
                              <div
                                key={sName}
                                className="flex items-center gap-1.5 text-[11px]"
                              >
                                {res.passed ? (
                                  <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                                ) : (
                                  <XCircle className="w-3 h-3 text-rose-400 shrink-0" />
                                )}
                                <span className="font-medium text-slate-200">{sName}:</span>
                                <span
                                  className={
                                    res.passed ? "text-emerald-400" : "text-rose-400"
                                  }
                                >
                                  {res.actual.replace("SKILL_", "")}
                                </span>
                              </div>
                            ))
                          )}
                        </div>
                      </td>

                      {/* Failure Reasons */}
                      <td className="py-3.5 px-4 max-w-xs">
                        {candidate.failure_reasons.length === 0 ? (
                          <span className="text-emerald-400 font-medium text-[11px]">
                            All criteria satisfied
                          </span>
                        ) : (
                          <ul className="space-y-1">
                            {candidate.failure_reasons.map((reason, i) => (
                              <li
                                key={i}
                                className="text-rose-300/90 text-[11px] leading-tight flex items-start gap-1"
                              >
                                <span className="text-rose-500 font-bold">•</span>
                                <span>{reason}</span>
                              </li>
                            ))}
                          </ul>
                        )}
                      </td>

                      {/* Action */}
                      <td className="py-3.5 px-4 text-right">
                        <NextLink
                          href={`/students/${candidate.student_id}`}
                          className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-[#182030] hover:bg-[#232D45] text-slate-300 hover:text-white border border-[#2D3A54] transition-colors"
                        >
                          <span>Inspect</span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </NextLink>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
