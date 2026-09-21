import React from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
} from "react-native";
import { useQuery } from "@tanstack/react-query";
import { fetchStudentProfile } from "../../api/students";
import { fetchMyEvidence } from "../../api/evidence";
import { fetchGitHubStatus } from "../../api/github";
import { fetchAvailableAssessments } from "../../api/assessments";
import { colors } from "../../theme/colors";
import { Card } from "../../components/common/Card";
import { SkillStatusBadge } from "../../components/skills/SkillStatusBadge";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import { ErrorBanner } from "../../components/common/ErrorBanner";
import {
  GraduationCap,
  FileCheck2,
  GitBranch,
  Award,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  ChevronRight,
} from "lucide-react-native";

interface DashboardScreenProps {
  navigation: any;
}

export const DashboardScreen: React.FC<DashboardScreenProps> = ({ navigation }) => {
  const {
    data: profile,
    isLoading: isProfileLoading,
    error: profileError,
    refetch: refetchProfile,
    isRefetching,
  } = useQuery({
    queryKey: ["profile"],
    queryFn: fetchStudentProfile,
  });

  const { data: evidenceList } = useQuery({
    queryKey: ["evidence"],
    queryFn: fetchMyEvidence,
  });

  const { data: githubStatus } = useQuery({
    queryKey: ["github-status"],
    queryFn: fetchGitHubStatus,
  });

  const { data: availableAssessments } = useQuery({
    queryKey: ["assessments-available"],
    queryFn: fetchAvailableAssessments,
  });

  const onRefresh = () => {
    refetchProfile();
  };

  if (isProfileLoading && !isRefetching) {
    return (
      <View style={styles.centerContainer}>
        <LoadingSpinner message="Loading your placement portfolio..." />
      </View>
    );
  }

  if (profileError) {
    return (
      <View style={styles.centerContainer}>
        <ErrorBanner
          message={(profileError as any).message || "Failed to load student profile."}
          onRetry={refetchProfile}
        />
      </View>
    );
  }

  const readyAssessmentsCount =
    availableAssessments?.filter((a) => a.practical_available || a.followup_available).length || 0;
  const verifiedSkillsCount =
    profile?.skills?.filter((s) => s.verification_status === "SKILL_VERIFIED").length || 0;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={isRefetching}
          onRefresh={onRefresh}
          tintColor={colors.primary}
          colors={[colors.primary]}
        />
      }
    >
      {/* Student Profile Card */}
      <Card style={styles.profileCard}>
        <View style={styles.profileHeader}>
          <View style={styles.avatarCircle}>
            <Text style={styles.avatarInitials}>
              {profile?.full_name
                ?.split(" ")
                .map((n) => n[0])
                .slice(0, 2)
                .join("")
                .toUpperCase() || "ST"}
            </Text>
          </View>
          <View style={styles.profileMeta}>
            <Text style={styles.studentName}>{profile?.full_name}</Text>
            <Text style={styles.collegeName}>{profile?.college_name}</Text>
            <View style={styles.pillRow}>
              <Text style={styles.branchPill}>
                {profile?.branch} • {profile?.qualification}
              </Text>
              <Text style={styles.cgpaPill}>CGPA: {profile?.cgpa?.toFixed(2)}</Text>
            </View>
          </View>
        </View>
      </Card>

      {/* Metrics Row */}
      <View style={styles.metricsRow}>
        <TouchableOpacity
          style={{ flex: 1 }}
          activeOpacity={0.7}
          onPress={() => navigation.navigate("Evidence")}
        >
          <Card style={styles.metricCard}>
            <FileCheck2 size={20} color={colors.accent} />
            <Text style={styles.metricValue}>{evidenceList?.length || 0}</Text>
            <Text style={styles.metricLabel}>Evidence Files</Text>
          </Card>
        </TouchableOpacity>

        <TouchableOpacity
          style={{ flex: 1 }}
          activeOpacity={0.7}
          onPress={() => navigation.navigate("Evidence")}
        >
          <Card style={styles.metricCard}>
            <GitBranch
              size={20}
              color={githubStatus?.is_connected ? colors.status.SKILL_VERIFIED.text : colors.textMuted}
            />
            <Text style={styles.metricValue}>
              {githubStatus?.is_connected ? "Connected" : "Not Linked"}
            </Text>
            <Text style={styles.metricLabel}>GitHub</Text>
          </Card>
        </TouchableOpacity>

        <TouchableOpacity
          style={{ flex: 1 }}
          activeOpacity={0.7}
          onPress={() => navigation.navigate("Assessments")}
        >
          <Card style={styles.metricCard}>
            <Award size={20} color={colors.status.SKILL_ASSESSED.text} />
            <Text style={styles.metricValue}>{readyAssessmentsCount}</Text>
            <Text style={styles.metricLabel}>Assessments</Text>
          </Card>
        </TouchableOpacity>
      </View>

      {/* Verification Overview */}
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>MVP Skills Verification</Text>
        <TouchableOpacity
          style={styles.seeAllRow}
          onPress={() => navigation.navigate("Skills")}
        >
          <Text style={styles.seeAllText}>View all</Text>
          <ChevronRight size={14} color={colors.primary} />
        </TouchableOpacity>
      </View>

      <Card style={styles.skillsCard}>
        {profile?.skills && profile.skills.length > 0 ? (
          profile.skills.map((skill) => (
            <TouchableOpacity
              key={skill.skill_id}
              style={styles.skillRow}
              activeOpacity={0.7}
              onPress={() => navigation.navigate("Skills", { selectedSkillId: skill.skill_id })}
            >
              <View style={styles.skillLeft}>
                <Text style={styles.skillName}>{skill.skill_name}</Text>
              </View>
              <SkillStatusBadge status={skill.verification_status} size="small" />
            </TouchableOpacity>
          ))
        ) : (
          <Text style={styles.emptyText}>No skills registered yet.</Text>
        )}
      </Card>

      {/* Call to Action Banner */}
      <Card style={styles.actionCard}>
        <View style={styles.actionIconContainer}>
          <ShieldCheck size={28} color={colors.accent} />
        </View>
        <View style={styles.actionTextContainer}>
          <Text style={styles.actionTitle}>
            {(evidenceList?.length || 0) === 0
              ? "Upload Document Evidence"
              : `${verifiedSkillsCount} of ${profile?.skills?.length || 4} Skills Verified`}
          </Text>
          <Text style={styles.actionSubtitle}>
            {(evidenceList?.length || 0) === 0
              ? "Submit certificate PDF or GitHub project evidence to transition your claimed skills to Evidence Supported."
              : "Complete your practical assessments and connect GitHub project evidence to unlock full placement verification."}
          </Text>
        </View>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => {
            if ((evidenceList?.length || 0) === 0) {
              navigation.navigate("Evidence");
            } else {
              navigation.navigate("Assessments");
            }
          }}
        >
          <ArrowRight size={18} color={colors.textWhite} />
        </TouchableOpacity>
      </Card>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bgDark,
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  centerContainer: {
    flex: 1,
    backgroundColor: colors.bgDark,
    alignItems: "center",
    justifyContent: "center",
    padding: 20,
  },
  profileCard: {
    padding: 18,
    marginBottom: 14,
  },
  profileHeader: {
    flexDirection: "row",
    alignItems: "center",
  },
  avatarCircle: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: "rgba(124, 58, 237, 0.2)",
    borderColor: colors.primary,
    borderWidth: 1.5,
    alignItems: "center",
    justifyContent: "center",
    marginRight: 14,
  },
  avatarInitials: {
    fontSize: 20,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  profileMeta: {
    flex: 1,
  },
  studentName: {
    fontSize: 19,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  collegeName: {
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: 2,
  },
  pillRow: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 6,
    gap: 6,
  },
  branchPill: {
    fontSize: 11,
    color: colors.textMuted,
    backgroundColor: "rgba(255,255,255,0.06)",
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
  },
  cgpaPill: {
    fontSize: 11,
    color: colors.accent,
    fontWeight: "600",
    backgroundColor: "rgba(6, 182, 212, 0.1)",
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
  },
  metricsRow: {
    flexDirection: "row",
    gap: 10,
    marginBottom: 14,
  },
  metricCard: {
    flex: 1,
    padding: 12,
    alignItems: "center",
    marginBottom: 0,
  },
  metricValue: {
    fontSize: 15,
    fontWeight: "700",
    color: colors.textPrimary,
    marginTop: 6,
  },
  metricLabel: {
    fontSize: 11,
    color: colors.textSecondary,
    marginTop: 2,
  },
  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 8,
    marginBottom: 10,
    paddingHorizontal: 2,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: colors.textPrimary,
  },
  seeAllRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
  },
  seeAllText: {
    fontSize: 13,
    color: colors.primary,
    fontWeight: "500",
  },
  skillsCard: {
    padding: 12,
    marginBottom: 14,
  },
  skillRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 10,
    paddingHorizontal: 6,
    borderBottomWidth: 1,
    borderBottomColor: "rgba(255,255,255,0.05)",
  },
  skillLeft: {
    flex: 1,
  },
  skillName: {
    fontSize: 15,
    fontWeight: "600",
    color: colors.textPrimary,
  },
  emptyText: {
    fontSize: 13,
    color: colors.textMuted,
    textAlign: "center",
    padding: 12,
  },
  actionCard: {
    flexDirection: "row",
    alignItems: "center",
    padding: 16,
    backgroundColor: "rgba(124, 58, 237, 0.08)",
    borderColor: "rgba(124, 58, 237, 0.3)",
  },
  actionIconContainer: {
    marginRight: 12,
  },
  actionTextContainer: {
    flex: 1,
  },
  actionTitle: {
    fontSize: 14,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  actionSubtitle: {
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 2,
    lineHeight: 16,
  },
  actionButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.primary,
    alignItems: "center",
    justifyContent: "center",
    marginLeft: 10,
  },
});
