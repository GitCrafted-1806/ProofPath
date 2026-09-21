"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { Shield, Lock, Mail, ArrowRight, Loader2, AlertCircle, Sparkles } from "lucide-react";

export default function LoginPage() {
  const { login, demoLogin, error, clearError } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    if (!email || !password) {
      setLocalError("Please enter both email and password.");
      return;
    }

    setIsSubmitting(true);
    try {
      await login(email, password);
    } catch (err: any) {
      setLocalError(err.message || "Failed to sign in. Please verify credentials.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDemoLogin = async () => {
    setLocalError(null);
    clearError();
    setEmail("coordinator@college.edu");
    setPassword("Password123!");
    setIsSubmitting(true);
    try {
      await demoLogin();
    } catch (err: any) {
      setLocalError(err.message || "Failed to execute demo login.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const activeError = localError || error;

  return (
    <div className="min-h-[80vh] flex flex-col justify-center items-center px-4">
      <div className="w-full max-w-md">
        {/* Brand Banner */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 to-cyan-500 shadow-xl shadow-indigo-500/20 mb-4">
            <Shield className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">ProofPath</h1>
          <p className="text-sm text-slate-400 mt-1">Placement Cell Coordinator Portal</p>
        </div>

        {/* Card */}
        <div className="bg-[#131926] border border-[#1F293D] rounded-2xl p-6 sm:p-8 shadow-2xl">
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-white">Coordinator Sign In</h2>
            <p className="text-xs text-slate-400 mt-1">
              Access verified student dossiers, define placement criteria, and run deterministic matching.
            </p>
          </div>

          {/* Error Alert */}
          {activeError && (
            <div className="mb-5 rounded-lg border border-rose-500/30 bg-rose-500/10 p-3.5 flex items-start gap-2.5 text-xs text-rose-300">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-400" />
              <div className="flex-1 leading-relaxed">{activeError}</div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Official Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="coordinator@college.edu"
                  required
                  className="w-full pl-9 pr-3.5 py-2.5 bg-[#0B0F17] border border-[#1F293D] rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  required
                  className="w-full pl-9 pr-3.5 py-2.5 bg-[#0B0F17] border border-[#1F293D] rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full mt-2 py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-sm flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 transition-all cursor-pointer"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Signing In...</span>
                </>
              ) : (
                <>
                  <span>Sign In as Coordinator</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Login */}
          <div className="mt-6 pt-6 border-t border-[#1F293D]">
            <div className="text-center mb-3">
              <span className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">
                Hackathon / Evaluator Access
              </span>
            </div>
            <button
              type="button"
              onClick={handleDemoLogin}
              disabled={isSubmitting}
              className="w-full py-2.5 px-4 rounded-lg bg-[#1B2336] hover:bg-[#232D45] border border-[#2D3A54] text-slate-200 hover:text-white text-xs font-medium flex items-center justify-center gap-2 transition-colors cursor-pointer"
            >
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              <span>One-Click Demo Coordinator Login</span>
            </button>
            <p className="text-[11px] text-center text-slate-500 mt-2">
              Auto-fills: <span className="text-slate-400 font-mono">coordinator@college.edu</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
