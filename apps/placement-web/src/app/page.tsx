"use client";

import React, { useEffect, useState, useCallback } from "react";
import NextLink from "next/link";
import { api, formatApiError, StudentDirectoryListResponse, PlacementRequirement } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { ErrorState, LoadingState } from "@/components/StatusFeedback";
import {
  Users,
  Briefcase,
  Award,
  CheckCircle2,
  ArrowUpRight,
  Activity,
  Search,
  PlusCircle,
  FileSpreadsheet,
} from "lucide-react";

export default function DashboardOverview() {
  const { user, token } = useAuth();
  const [studentsData, setStudentsData] = useState<StudentDirectoryListResponse | null>(null);
  const [requirements, setRequirements] = useState<PlacementRequirement[]>([]);
  const [demoStatus, setDemoStatus] = useState<any>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    setError(null);

    try {
      const [studentsRes, reqsRes, demoRes] = await Promise.all([
        api.get<StudentDirectoryListResponse>("/api/v1/students?limit=100"),
        api.get<PlacementRequirement[]>("/api/v1/placements/requirements"),
        api.get("/api/v1/demo/status").catch(() => ({ data: { demo_mode: false } })),
      ]);

      setStudentsData(studentsRes.data);
      setRequirements(reqsRes.data);
      setDemoStatus(demoRes.data);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  if (isLoading) {
    return <LoadingState message="Loading coordinator metrics and candidates..." />;
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between pb-4 border-b border-[#1F293D]">
          <div>
            <h1 className="text-xl font-bold text-white">Placement Cell Overview</h1>
            <p className="text-xs text-slate-400">Deterministic candidate verification operations</p>
          </div>
        </div>
        <ErrorState
          title="Backend Connection Error"
          message={error}
          onRetry={fetchDashboardData}
        />
      </div>
    );
  }

  const totalStudents = studentsData?.total || 0;
  const verifiedCount =
    studentsData?.students.reduce((acc, s) => acc + (s.verified_skills_count > 0 ? 1 : 0), 0) || 0;
  const totalVerifiedSkills =
    studentsData?.students.reduce((acc, s) => acc + s.verified_skills_count, 0) || 0;

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-[#1F293D]">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Placement Cell Overview</h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time candidate verification telemetry & deterministic matching engine
          </p>
        </div>

        {/* Status Indicator */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>FastAPI Engine Active</span>
          </div>
          {demoStatus?.demo_mode && (
            <span className="px-2.5 py-1 rounded-md bg-indigo-500/10 border border-indigo-500/20 text-[11px] font-mono text-indigo-300">
              Demo Fixtures Active
            </span>
          )}
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#131926] border border-[#1F293D] rounded-xl p-5">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-medium uppercase tracking-wider">Registered Students</span>
            <Users className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-white">{totalStudents}</div>
          <p className="text-xs text-slate-500 mt-1">Total candidate dossiers in system</p>
        </div>

        <div className="bg-[#131926] border border-[#1F293D] rounded-xl p-5">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-medium uppercase tracking-wider">Verified Candidates</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400">{verifiedCount}</div>
          <p className="text-xs text-slate-500 mt-1">Students with ≥1 verified skill</p>
        </div>

        <div className="bg-[#131926] border border-[#1F293D] rounded-xl p-5">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-medium uppercase tracking-wider">Skill Verifications</span>
            <Award className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-cyan-400">{totalVerifiedSkills}</div>
          <p className="text-xs text-slate-500 mt-1">Deterministic multi-factor verified</p>
        </div>

        <div className="bg-[#131926] border border-[#1F293D] rounded-xl p-5">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-medium uppercase tracking-wider">Active Requirements</span>
            <Briefcase className="w-4 h-4 text-violet-400" />
          </div>
          <div className="text-2xl font-bold text-white">{requirements.length}</div>
          <p className="text-xs text-slate-500 mt-1">Corporate recruitment profiles</p>
        </div>
      </div>

      {/* Quick Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <NextLink
          href="/students"
          className="group block bg-[#131926] hover:bg-[#182030] border border-[#1F293D] hover:border-indigo-500/50 rounded-xl p-6 transition-all"
        >
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 rounded-lg bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-4">
              <Search className="w-5 h-5" />
            </div>
            <ArrowUpRight className="w-5 h-5 text-slate-500 group-hover:text-indigo-400 transition-colors" />
          </div>
          <h3 className="text-base font-semibold text-white group-hover:text-indigo-300 transition-colors">
            Student Directory & Dossiers
          </h3>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">
            Search students across branches and CGPA cutoffs. Inspect institutional certificates, GitHub project evidence, and assessment history.
          </p>
        </NextLink>

        <NextLink
          href="/requirements"
          className="group block bg-[#131926] hover:bg-[#182030] border border-[#1F293D] hover:border-cyan-500/50 rounded-xl p-6 transition-all"
        >
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 rounded-lg bg-cyan-600/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 mb-4">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <ArrowUpRight className="w-5 h-5 text-slate-500 group-hover:text-cyan-400 transition-colors" />
          </div>
          <h3 className="text-base font-semibold text-white group-hover:text-cyan-300 transition-colors">
            Placement Criteria & Deterministic Matching
          </h3>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">
            Define corporate recruitment criteria (CGPA, branch, required skill verification levels). Match candidates deterministically with zero AI hallucination or ranking bias.
          </p>
        </NextLink>
      </div>

      {/* Recent Requirements Section */}
      <div className="bg-[#131926] border border-[#1F293D] rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-white">Active Placement Requirements</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Configured criteria for upcoming recruitment drives
            </p>
          </div>
          <NextLink
            href="/requirements"
            className="text-xs font-medium text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
          >
            <span>View All</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </NextLink>
        </div>

        {requirements.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-xs">
            No placement requirements defined yet. Click "Placement Matching" to configure your first criteria.
          </div>
        ) : (
          <div className="divide-y divide-[#1F293D]">
            {requirements.slice(0, 3).map((req) => (
              <div key={req.id} className="py-3 flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-white">
                    {req.company_name} — <span className="text-slate-300">{req.role_title}</span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-slate-400 mt-1">
                    <span>Min CGPA: {req.min_cgpa.toFixed(1)}</span>
                    <span>•</span>
                    <span>Branches: {req.eligible_branches.join(", ") || "All"}</span>
                  </div>
                </div>
                <NextLink
                  href={`/requirements/${req.id}/match`}
                  className="px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-medium transition-colors"
                >
                  Run Match
                </NextLink>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
