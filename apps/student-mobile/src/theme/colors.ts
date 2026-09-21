/**
 * ProofPath dark design system color tokens
 */
export const colors = {
  bgDark: "#0B0F17",
  cardDark: "#131926",
  cardElevated: "#182032",
  borderDark: "#1E293B",
  borderHighlight: "#334155",

  primary: "#7C3AED",
  primaryHover: "#6D28D9",
  primaryGradient: ["#7C3AED", "#6366F1"],
  secondary: "#6366F1",
  accent: "#06B6D4",
  accentGlow: "rgba(6, 182, 212, 0.2)",

  textPrimary: "#F8FAFC",
  textSecondary: "#94A3B8",
  textMuted: "#64748B",
  textWhite: "#FFFFFF",

  // Verification status color mappings
  status: {
    SKILL_VERIFIED: {
      text: "#10B981",
      border: "#059669",
      bg: "rgba(16, 185, 129, 0.12)",
      label: "Skill Verified",
      icon: "check-circle",
    },
    SKILL_ASSESSED: {
      text: "#3B82F6",
      border: "#2563EB",
      bg: "rgba(59, 130, 246, 0.12)",
      label: "Skill Assessed",
      icon: "award",
    },
    EVIDENCE_SUPPORTED: {
      text: "#F59E0B",
      border: "#D97706",
      bg: "rgba(245, 158, 11, 0.12)",
      label: "Evidence Supported",
      icon: "file-check",
    },
    UNVERIFIED: {
      text: "#94A3B8",
      border: "#475569",
      bg: "rgba(100, 116, 139, 0.12)",
      label: "Unverified",
      icon: "circle",
    },
  },

  // Authenticity status
  authenticity: {
    SUBMITTED: { text: "#F59E0B", bg: "rgba(245, 158, 11, 0.12)" },
    SOURCE_SUPPORTED: { text: "#06B6D4", bg: "rgba(6, 182, 212, 0.12)" },
    INSTITUTION_VERIFIED: { text: "#10B981", bg: "rgba(16, 185, 129, 0.12)" },
    REJECTED: { text: "#EF4444", bg: "rgba(239, 68, 68, 0.12)" },
  },

  error: "#EF4444",
  errorBg: "rgba(239, 68, 68, 0.12)",
  success: "#10B981",
  warning: "#F59E0B",
  info: "#3B82F6",
};
