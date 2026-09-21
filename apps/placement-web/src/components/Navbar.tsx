"use client";

import React from "react";
import Link from "next/navigation";
import NextLink from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { Shield, Users, Briefcase, LayoutDashboard, LogOut, CheckCircle } from "lucide-react";

export function Navbar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();

  if (pathname === "/login") {
    return null;
  }

  const navItems = [
    { label: "Overview", href: "/", icon: LayoutDashboard },
    { label: "Student Directory", href: "/students", icon: Users },
    { label: "Placement Matching", href: "/requirements", icon: Briefcase },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-[#1F293D] bg-[#0B0F17]/90 backdrop-blur">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-6">
          <NextLink href="/" className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight text-white">ProofPath</span>
              <span className="ml-2 text-xs font-semibold px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                Placement Cell
              </span>
            </div>
          </NextLink>

          {/* Navigation links */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
              return (
                <NextLink
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-[#1E293B] text-white border border-[#334155]"
                      : "text-slate-400 hover:text-white hover:bg-[#131926]"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </NextLink>
              );
            })}
          </nav>
        </div>

        {/* User Identity & Logout */}
        {user && (
          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-[#131926] border border-[#1F293D] text-xs text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="font-mono">{user.email}</span>
            </div>
            <button
              onClick={logout}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-400 hover:text-white bg-[#131926] hover:bg-[#1E293B] border border-[#1F293D] rounded-md transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Logout</span>
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
