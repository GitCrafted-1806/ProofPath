import React from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Share,
} from "react-native";
import { useQuery } from "@tanstack/react-query";
import { fetchStudentProfile } from "../../api/students";
import { fetchMyEvidence } from "../../api/evidence";
import { fetchGitHubEvidence } from "../../api/github";
import { fetchAssessmentHistory } from "../../api/assessments";
import { colors } from "../../theme/colors";
import { Card } from "../../components/common/Card";
import { SkillStatusBadge } from "../../components/skills/SkillStatusBadge";
import { Button } from "../../components/common/Button";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import {
  ShieldCheck,
  Share2,
  CheckCircle2,
  FileText,
  GitBranch,
  Award,
  ArrowLeft,
  ExternalLink,
} from "lucide-react-native";

interface VerificationProfileScreenProps {
  navigation: any;
}

export const VerificationProfileScreen: React.FC<VerificationProfileScreenProps> = ({
  navigation,
}) => {
  const { data: profile, isLoading } = useQuery({
    queryKey: ["profile"],
    queryFn: fetchStudentProfile,
  });

  const { data: evidenceList } = useQuery({
    queryKey: ["evidence"],
    queryFn: fetchMyEvidence,
  });

  const { data: githubEvidence } = useQuery({
    queryKey: ["github-evidence"],
    queryFn: fetchGitHubEvidence,
  });

  const { data: assessmentsHistory } = useQuery({
    queryKey: ["assessments-history"],
    queryFn: fetchAssessmentHistory,
  });

  const handleShare = async () => {
    if (!profile) return;
    try {
      await Share.share({
        title: `${profile.full_name}'s Verified Skills Portfolio`,
        message: `View ${profile.full_name}'s verified technical skill portfolio on ProofPath: https://proofpath.edu/verify/${profile.public_profile_id}`,
      });
    } catch {
      Alert.alert("Link Copied", `Verification Token: ${profile.public_profile_id}`);
    }
  };

  if (isLoading) {
    return (
      <View style={styles.centerContainer}>
        <LoadingSpinner message="Generating verification portfolio..." />
      </View>
    );
  }

  const skills = profile?.skills || [];
  const verifiedSkills = skills.filter((s) => s.verification_status === "SKILL_VERIFIED");

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <TouchableOpacity style={styles.backRow} onPress={() => navigation.goBack()}>
        <ArrowLeft size={18} color={colors.textSecondary} />
        <Text style={styles.backText}>Back to Dashboard</Text>
      </TouchableOpacity>

      {/* Official Verified Resume Banner */}
      <Card style={styles.heroCard}>
        <View style={styles.shieldBadge}>
          <ShieldCheck size={36} color={colors.status.SKILL_VERIFIED.text} />
        </View>

        <Text style={styles.studentName}>{profile?.full_name}</Text>
        <Text style={styles.collegeText}>
          {profile?.college_name} • {profile?.branch}
        </Text>

        <View style={styles.metaRow}>
          <Text style={styles.metaItem}>CGPA: {profile?.cgpa?.toFixed(2)}</Text>
          <Text style={styles.dot}>•</Text>
          <Text style={styles.metaItem}>Class of {profile?.academic_year}</Text>
          <Text style={styles.dot}>•</Text>
          <Text style={styles.metaItem}>
            {verifiedSkills.length} Verified Skills
          </Text>
        </View>

        <View style={styles.publicIdBox}>
          <Text style={styles.publicIdLabel}>Public Verification ID:</Text>
          <Text style={styles.publicIdCode}>{profile?.public_profile_id}</Text>
        </View>

        <Button
          title="Share Resume Verification Link"
          onPress={handleShare}
          icon={<Share2 size={16} color={colors.textWhite} />}
          style={styles.shareBtn}
        />
      </Card>

      <Text style={styles.sectionTitle}>Verified Technical Skills Portfolio</Text>

      {skills.map((skill) => {
        const cert = evidenceList?.find(
          (e) =>
            (e.type === "CERTIFICATE" || e.type === "PROJECT_DOCUMENT") &&
            e.mapped_skills?.includes(skill.skill_name)
        );

        const project = githubEvidence?.find(
          (e) => e.type === "GITHUB_REPO" && e.mapped_skills?.includes(skill.skill_name)
        );

        const practical = assessmentsHistory?.find(
          (a) => a.skill_name === skill.skill_name && a.type === "PRACTICAL" && a.passed
        );

        const followup = assessmentsHistory?.find(
          (a) => a.skill_name === skill.skill_name && a.type === "FOLLOW_UP" && a.passed
        );

        return (
          <Card key={skill.skill_id} style={styles.skillPortfolioCard}>
            <View style={styles.skillHeader}>
              <Text style={styles.skillName}>{skill.skill_name}</Text>
              <SkillStatusBadge status={skill.verification_status} />
            </View>

            <View style={styles.evidenceChain}>
              {/* Certificate */}
              <View style={styles.chainItem}>
                <FileText
                  size={16}
                  color={cert ? colors.status.SKILL_VERIFIED.text : colors.textMuted}
                />
                <Text style={styles.chainLabel}>Supporting Evidence:</Text>
                <Text style={styles.chainValue} numberOfLines={1}>
                  {cert?.original_filename || "None linked"}
                </Text>
              </View>

              {/* Practical Assessment */}
              <View style={styles.chainItem}>
                <Award
                  size={16}
                  color={practical ? colors.status.SKILL_VERIFIED.text : colors.textMuted}
                />
                <Text style={styles.chainLabel}>Practical Assessment:</Text>
                <Text style={styles.chainValue}>
                  {practical ? `Passed (${practical.score}%)` : "Not completed"}
                </Text>
              </View>

              {/* GitHub Repo */}
              <View style={styles.chainItem}>
                <GitBranch
                  size={16}
                  color={project ? colors.status.SKILL_VERIFIED.text : colors.textMuted}
                />
                <Text style={styles.chainLabel}>GitHub Project:</Text>
                <Text style={styles.chainValue} numberOfLines={1}>
                  {project?.original_filename || "None linked"}
                </Text>
              </View>

              {/* Follow-up Assessment */}
              <View style={styles.chainItem}>
                <CheckCircle2
                  size={16}
                  color={followup ? colors.status.SKILL_VERIFIED.text : colors.textMuted}
                />
                <Text style={styles.chainLabel}>Follow-up Verification:</Text>
                <Text style={styles.chainValue}>
                  {followup ? "Verified by Engine" : "Pending"}
                </Text>
              </View>
            </View>
          </Card>
        );
      })}
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
    paddingBottom: 40,
  },
  centerContainer: {
    flex: 1,
    backgroundColor: colors.bgDark,
    alignItems: "center",
    justifyContent: "center",
    padding: 20,
  },
  backRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 14,
  },
  backText: {
    fontSize: 13,
    color: colors.textSecondary,
    marginLeft: 6,
  },
  heroCard: {
    alignItems: "center",
    padding: 24,
    backgroundColor: "rgba(16, 185, 129, 0.05)",
    borderColor: "rgba(16, 185, 129, 0.3)",
    marginBottom: 20,
  },
  shieldBadge: {
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: "rgba(16, 185, 129, 0.15)",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 12,
  },
  studentName: {
    fontSize: 22,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  collegeText: {
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: 2,
    textAlign: "center",
  },
  metaRow: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 8,
    gap: 8,
  },
  metaItem: {
    fontSize: 12,
    color: colors.accent,
    fontWeight: "600",
  },
  dot: {
    color: colors.textMuted,
    fontSize: 12,
  },
  publicIdBox: {
    backgroundColor: colors.cardElevated,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginTop: 14,
    alignItems: "center",
  },
  publicIdLabel: {
    fontSize: 11,
    color: colors.textMuted,
  },
  publicIdCode: {
    fontFamily: "monospace",
    fontSize: 13,
    color: colors.textPrimary,
    fontWeight: "600",
    marginTop: 2,
  },
  shareBtn: {
    marginTop: 16,
    width: "100%",
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: colors.textPrimary,
    marginBottom: 12,
  },
  skillPortfolioCard: {
    padding: 16,
    marginBottom: 12,
  },
  skillHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  skillName: {
    fontSize: 17,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  evidenceChain: {
    gap: 8,
    borderTopWidth: 1,
    borderTopColor: "rgba(255,255,255,0.05)",
    paddingTop: 10,
  },
  chainItem: {
    flexDirection: "row",
    alignItems: "center",
  },
  chainLabel: {
    fontSize: 12,
    color: colors.textSecondary,
    marginLeft: 8,
    width: 135,
  },
  chainValue: {
    fontSize: 12,
    color: colors.textPrimary,
    flex: 1,
    fontWeight: "500",
  },
});
