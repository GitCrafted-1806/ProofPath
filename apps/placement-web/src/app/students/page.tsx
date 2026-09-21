"use client";

import React, { useState, useEffect, useCallback } from "react";
import NextLink from "next/link";
import {
  api,
  formatApiError,
  StudentDirectoryItem,
  StudentDirectoryListResponse,
  SkillVerificationStatus,
} from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { ErrorState, LoadingState, EmptyState } from "@/components/StatusFeedback";
import {
  Search,
  Filter,
  GraduationCap,
  Award,
  ChevronRight,
  RefreshCw,
  ExternalLink,
} from "lucide-react";

export default function StudentsDirectoryPage() {
  const { token } = useAuth();
  const [students, setStudents] = useState<StudentDirectoryItem[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [selectedBranch, setSelectedBranch] = useState<string>("");
  const [minCgpa, setMinCgpa] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStudents = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (searchTerm.trim()) params.append("search", searchTerm.trim());
      if (selectedBranch) params.append("branch", selectedBranch);
      if (minCgpa) params.append("min_cgpa", minCgpa);
      params.append("limit", "100");

      const response = await api.get<StudentDirectoryListResponse>(
        `/api/v1/students?${params.toString()}`
      );
      setStudents(response.data.students);
      setTotalCount(response.data.total);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setIsLoading(false);
    }
  }, [token, searchTerm, selectedBranch, minCgpa]);

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchStudents();
    }, 250);
    return () => clearTimeout(timer);
  }, [fetchStudents]);

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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-[#1F293D]">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Student Directory</h1>
          <p className="text-sm text-slate-400 mt-1">
            Browse verified academic dossiers, authenticated credentials, and assessment records
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span>Total Candidates:</span>
          <span className="font-semibold text-white bg-[#131926] px-2.5 py-1 rounded-md border border-[#1F293D]">
            {totalCount}
          </span>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-[#131926] border border-[#1F293D] rounded-xl p-4">
        <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
          {/* Search */}
          <div className="sm:col-span-6 relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by student name, college, or email..."
              className="w-full pl-9 pr-3.5 py-2 bg-[#0B0F17] border border-[#1F293D] rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </div>

          {/* Branch Filter */}
          <div className="sm:col-span-3">
            <select
              value={selectedBranch}
              onChange={(e) => setSelectedBranch(e.target.value)}
              className="w-full px-3 py-2 bg-[#0B0F17] border border-[#1F293D] rounded-lg text-xs text-white focus:outline-none focus:border-indigo-500 transition-colors cursor-pointer"
            >
              <option value="">All Branches</option>
              <option value="CSE">Computer Science (CSE)</option>
              <option value="IT">Information Technology (IT)</option>
              <option value="ECE">Electronics (ECE)</option>
              <option value="EE">Electrical (EE)</option>
              <option value="ME">Mechanical (ME)</option>
            </select>
          </div>

          {/* Min CGPA Filter */}
          <div className="sm:col-span-3">
            <select
              value={minCgpa}
              onChange={(e) => setMinCgpa(e.target.value)}
              className="w-full px-3 py-2 bg-[#0B0F17] border border-[#1F293D] rounded-lg text-xs text-white focus:outline-none focus:border-indigo-500 transition-colors cursor-pointer"
            >
              <option value="">Any CGPA</option>
              <option value="6.0">≥ 6.0 CGPA</option>
              <option value="7.0">≥ 7.0 CGPA</option>
              <option value="7.5">≥ 7.5 CGPA</option>
              <option value="8.0">≥ 8.0 CGPA</option>
              <option value="8.5">≥ 8.5 CGPA</option>
              <option value="9.0">≥ 9.0 CGPA</option>
            </select>
          </div>
        </div>
      </div>

      {/* Content Area */}
      {isLoading ? (
        <LoadingState message="Fetching student directory from backend..." />
      ) : error ? (
        <ErrorState
          title="Directory Query Failed"
          message={error}
          onRetry={fetchStudents}
        />
      ) : students.length === 0 ? (
        <EmptyState
          title="No Candidates Found"
          description="No student profiles match your search criteria. Try adjusting the branch, CGPA cutoff, or search query."
          actionLabel="Clear Filters"
          onAction={() => {
            setSearchTerm("");
            setSelectedBranch("");
            setMinCgpa("");
          }}
        />
      ) : (
        <div className="bg-[#131926] border border-[#1F293D] rounded-xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-[#0B0F17] text-slate-400 uppercase tracking-wider text-[11px] border-b border-[#1F293D]">
                <tr>
                  <th className="py-3.5 px-4 font-semibold">Student Name</th>
                  <th className="py-3.5 px-4 font-semibold">Branch & College</th>
                  <th className="py-3.5 px-4 font-semibold">CGPA</th>
                  <th className="py-3.5 px-4 font-semibold">Skill Verification Profile</th>
                  <th className="py-3.5 px-4 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1F293D]">
                {students.map((student) => (
                  <tr
                    key={student.id}
                    className="hover:bg-[#182030]/60 transition-colors"
                  >
                    {/* Student Info */}
                    <td className="py-3.5 px-4">
                      <div className="font-medium text-white text-sm">
                        {student.full_name}
                      </div>
                      <div className="text-slate-400 font-mono text-[11px] mt-0.5">
                        {student.email}
                      </div>
                    </td>

                    {/* Branch & College */}
                    <td className="py-3.5 px-4">
                      <div className="font-medium text-slate-200">
                        {student.branch} ({student.qualification})
                      </div>
                      <div className="text-slate-400 text-[11px] mt-0.5">
                        {student.college_name} • Class of {student.academic_year}
                      </div>
                    </td>

                    {/* CGPA */}
                    <td className="py-3.5 px-4">
                      <span className="font-semibold text-white px-2 py-1 rounded bg-[#0B0F17] border border-[#1F293D]">
                        {student.cgpa.toFixed(2)}
                      </span>
                    </td>

                    {/* Skill Badges */}
                    <td className="py-3.5 px-4">
                      <div className="flex flex-wrap gap-1.5 max-w-md">
                        {student.skills.length === 0 ? (
                          <span className="text-slate-500 italic">No skills registered</span>
                        ) : (
                          student.skills.map((s) => (
                            <span
                              key={s.skill_id}
                              className={`px-2 py-0.5 rounded text-[10px] font-medium border ${getStatusBadge(
                                s.verification_status
                              )}`}
                            >
                              {s.skill_name}: {s.verification_status.replace("SKILL_", "")}
                            </span>
                          ))
                        )}
                      </div>
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-4 text-right">
                      <NextLink
                        href={`/students/${student.id}`}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 font-medium transition-colors"
                      >
                        <span>View Dossier</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </NextLink>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
