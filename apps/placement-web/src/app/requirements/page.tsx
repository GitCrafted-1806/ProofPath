"use client";

import React, { useState, useEffect, useCallback } from "react";
import NextLink from "next/link";
import {
  api,
  formatApiError,
  PlacementRequirement,
  PlacementRequirementCreate,
} from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { ErrorState, LoadingState, EmptyState } from "@/components/StatusFeedback";
import {
  Briefcase,
  Plus,
  Trash2,
  ArrowRight,
  Loader2,
  Building,
  GraduationCap,
  Award,
  Sparkles,
  CheckCircle2,
} from "lucide-react";

const MVP_SKILLS = ["Python", "Pandas", "Matplotlib", "Git/GitHub"];
const BRANCH_OPTIONS = ["CSE", "IT", "ECE", "EE", "ME"];
const VERIFICATION_LEVELS = [
  { value: "SKILL_VERIFIED", label: "Verified (Full Multi-Factor)" },
  { value: "SKILL_ASSESSED", label: "Assessed (Evidence + Test Passed)" },
  { value: "EVIDENCE_SUPPORTED", label: "Evidence Supported (Cert/Doc)" },
];

export default function PlacementRequirementsPage() {
  const { token } = useAuth();
  const [requirements, setRequirements] = useState<PlacementRequirement[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Creation Modal State
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [companyName, setCompanyName] = useState<string>("");
  const [roleTitle, setRoleTitle] = useState<string>("");
  const [minCgpa, setMinCgpa] = useState<number>(7.0);
  const [selectedBranches, setSelectedBranches] = useState<string[]>(["CSE", "IT"]);
  const [requiredSkills, setRequiredSkills] = useState<Record<string, string>>({
    Python: "SKILL_VERIFIED",
  });
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const fetchRequirements = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.get<PlacementRequirement[]>("/api/v1/placements/requirements");
      setRequirements(res.data);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchRequirements();
  }, [fetchRequirements]);

  const handleDelete = async (reqId: string, company: string) => {
    if (!confirm(`Are you sure you want to delete the placement requirement for ${company}?`)) {
      return;
    }
    try {
      await api.delete(`/api/v1/placements/requirements/${reqId}`);
      setRequirements((prev) => prev.filter((r) => r.id !== reqId));
    } catch (err) {
      alert(`Failed to delete requirement: ${formatApiError(err)}`);
    }
  };

  const handleBranchToggle = (branch: string) => {
    setSelectedBranches((prev) =>
      prev.includes(branch) ? prev.filter((b) => b !== branch) : [...prev, branch]
    );
  };

  const handleSkillToggle = (skill: string) => {
    setRequiredSkills((prev) => {
      const copy = { ...prev };
      if (copy[skill]) {
        delete copy[skill];
      } else {
        copy[skill] = "SKILL_VERIFIED";
      }
      return copy;
    });
  };

  const handleSkillLevelChange = (skill: string, level: string) => {
    setRequiredSkills((prev) => ({
      ...prev,
      [skill]: level,
    }));
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const comp = companyName.trim();
    if (!comp) {
      setCreateError("Please enter a company name.");
      return;
    }
    if (comp.length < 2 || comp.length > 120) {
      setCreateError("Company name must be between 2 and 120 characters.");
      return;
    }

    const role = roleTitle.trim();
    if (!role) {
      setCreateError("Please enter a role title.");
      return;
    }
    if (role.length < 2 || role.length > 100) {
      setCreateError("Role title must be between 2 and 100 characters.");
      return;
    }

    const cgpaNum = Number(minCgpa);
    if (isNaN(cgpaNum) || cgpaNum < 0 || cgpaNum > 10) {
      setCreateError("Minimum CGPA must be between 0.00 and 10.00.");
      return;
    }

    setIsSubmitting(true);
    setCreateError(null);

    const payload: PlacementRequirementCreate = {
      company_name: comp,
      role_title: role,
      min_cgpa: Math.round(cgpaNum * 100) / 100,
      eligible_branches: selectedBranches.filter((b) => b.trim().length > 0),
      required_skills: requiredSkills,
    };

    try {
      await api.post("/api/v1/placements/requirements", payload);
      await fetchRequirements();
      setIsModalOpen(false);
      // Reset
      setCompanyName("");
      setRoleTitle("");
      setMinCgpa(7.0);
      setSelectedBranches(["CSE", "IT"]);
      setRequiredSkills({ Python: "SKILL_VERIFIED" });
    } catch (err) {
      setCreateError(formatApiError(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-[#1F293D]">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Placement Criteria & Recruitment Drives
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Define corporate requirements and evaluate candidates via deterministic matching
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>Create Requirement</span>
        </button>
      </div>

      {/* Content */}
      {isLoading ? (
        <LoadingState message="Loading corporate placement requirements..." />
      ) : error ? (
        <ErrorState
          title="Could Not Load Requirements"
          message={error}
          onRetry={fetchRequirements}
        />
      ) : requirements.length === 0 ? (
        <EmptyState
          title="No Placement Requirements Configured"
          description="Create a recruitment requirement with CGPA, branch, and required skill verification levels to begin deterministic candidate matching."
          actionLabel="Create First Requirement"
          onAction={() => setIsModalOpen(true)}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {requirements.map((req) => (
            <div
              key={req.id}
              className="bg-[#131926] border border-[#1F293D] rounded-xl p-6 flex flex-col justify-between shadow-xl"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h2 className="text-lg font-bold text-white">{req.company_name}</h2>
                    <p className="text-sm text-slate-300 font-medium">{req.role_title}</p>
                  </div>
                  <button
                    onClick={() => handleDelete(req.id, req.company_name)}
                    className="p-1.5 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors cursor-pointer"
                    title="Delete Requirement"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <div className="mt-4 space-y-2 text-xs text-slate-400">
                  <div className="flex items-center justify-between py-1.5 border-b border-[#1F293D]/60">
                    <span className="flex items-center gap-1.5">
                      <GraduationCap className="w-3.5 h-3.5 text-slate-500" />
                      Min CGPA:
                    </span>
                    <span className="font-semibold text-white">{req.min_cgpa.toFixed(2)}</span>
                  </div>

                  <div className="flex items-center justify-between py-1.5 border-b border-[#1F293D]/60">
                    <span>Eligible Branches:</span>
                    <span className="font-medium text-slate-200">
                      {req.eligible_branches.length > 0
                        ? req.eligible_branches.join(", ")
                        : "All Branches"}
                    </span>
                  </div>

                  <div className="pt-2">
                    <span className="text-[11px] font-semibold text-slate-300 block mb-1.5">
                      Required Skill Verifications:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {Object.keys(req.required_skills).length === 0 ? (
                        <span className="text-slate-500 italic">None specified</span>
                      ) : (
                        Object.entries(req.required_skills).map(([skill, level]) => (
                          <span
                            key={skill}
                            className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#0B0F17] text-indigo-300 border border-indigo-500/30"
                          >
                            {skill}: {level.replace("SKILL_", "")}
                          </span>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Match Action */}
              <div className="mt-6 pt-4 border-t border-[#1F293D] flex items-center justify-between">
                <span className="text-[11px] text-slate-500 font-mono">
                  Created {new Date(req.created_at).toLocaleDateString()}
                </span>
                <NextLink
                  href={`/requirements/${req.id}/match`}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all"
                >
                  <span>Deterministic Match</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </NextLink>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Requirement Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-[#131926] border border-[#1F293D] rounded-2xl max-w-lg w-full p-6 shadow-2xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold text-white mb-1">Create Placement Requirement</h3>
            <p className="text-xs text-slate-400 mb-4">
              Specify explicit recruitment criteria for binary deterministic compliance.
            </p>

            {createError && (
              <div className="mb-4 rounded-lg bg-rose-500/10 border border-rose-500/30 p-3 text-xs text-rose-300">
                {createError}
              </div>
            )}

            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Company Name
                  </label>
                  <input
                    type="text"
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    placeholder="e.g. Google, Microsoft, Infosys"
                    required
                    className="w-full px-3 py-2 bg-[#0B0F17] border border-[#1F293D] rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Role Title
                  </label>
                  <input
                    type="text"
                    value={roleTitle}
                    onChange={(e) => setRoleTitle(e.target.value)}
                    placeholder="e.g. Associate Software Engineer"
                    required
                    className="w-full px-3 py-2 bg-[#0B0F17] border border-[#1F293D] rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Minimum CGPA Cutoff: <strong className="text-white">{minCgpa.toFixed(1)}</strong>
                </label>
                <input
                  type="range"
                  min="5.0"
                  max="9.5"
                  step="0.1"
                  value={minCgpa}
                  onChange={(e) => setMinCgpa(parseFloat(e.target.value))}
                  className="w-full accent-indigo-600 cursor-pointer"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Eligible Branches
                </label>
                <div className="flex flex-wrap gap-2">
                  {BRANCH_OPTIONS.map((branch) => {
                    const selected = selectedBranches.includes(branch);
                    return (
                      <button
                        type="button"
                        key={branch}
                        onClick={() => handleBranchToggle(branch)}
                        className={`px-3 py-1 rounded-md text-xs font-medium border transition-colors ${
                          selected
                            ? "bg-indigo-600/30 text-indigo-300 border-indigo-500/50"
                            : "bg-[#0B0F17] text-slate-400 border-[#1F293D]"
                        }`}
                      >
                        {branch}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Required Skills & Verification Level
                </label>
                <div className="space-y-2">
                  {MVP_SKILLS.map((skill) => {
                    const isRequired = !!requiredSkills[skill];
                    return (
                      <div
                        key={skill}
                        className="flex items-center justify-between p-2.5 rounded-lg bg-[#0B0F17] border border-[#1F293D]"
                      >
                        <label className="flex items-center gap-2 text-xs font-medium text-white cursor-pointer">
                          <input
                            type="checkbox"
                            checked={isRequired}
                            onChange={() => handleSkillToggle(skill)}
                            className="accent-indigo-600 rounded"
                          />
                          <span>{skill}</span>
                        </label>

                        {isRequired && (
                          <select
                            value={requiredSkills[skill] || "SKILL_VERIFIED"}
                            onChange={(e) => handleSkillLevelChange(skill, e.target.value)}
                            className="px-2 py-1 bg-[#131926] border border-[#1F293D] rounded text-[11px] text-indigo-300 focus:outline-none cursor-pointer"
                          >
                            {VERIFICATION_LEVELS.map((lvl) => (
                              <option key={lvl.value} value={lvl.value}>
                                {lvl.label}
                              </option>
                            ))}
                          </select>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#1F293D]">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg bg-[#1B2336] text-slate-300 hover:text-white text-xs font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Saving...</span>
                    </>
                  ) : (
                    <span>Save Requirement</span>
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
