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
import { fetchGitHubEvidence, fetchGitHubStatus } from "../../api/github";
import { fetchAvailableAssessments } from "../../api/assessments";
import { colors } from "../../theme/colors";
import { Card } from "../../components/common/Card";
import { SkillStatusBadge } from "../../components/skills/SkillStatusBadge";
import { Button } from "../../components/common/Button";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import {
  CheckCircle2,
  XCircle,
  FileCheck,
  Award,
  GitBranch,
  ShieldCheck,
  ArrowLeft,
  ChevronRight,
} from "lucide-react-native";

interface SkillDetailScreenProps {
  route: any;
  navigation: any;
}

export const SkillDetailScreen: React.FC<SkillDetailScreenProps> = ({
  route,
  navigation,
}) => {
  const { skillId, skillName } = route.params;

  const { data: profile, refetch: refetchProfile, isRefetching } = useQuery({
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

  const { data: availableAssessments } = useQuery({
    queryKey: ["assessments-available"],
    queryFn: fetchAvailableAssessments,
  });

  const studentSkill = profile?.skills?.find((s) => s.skill_id === skillId);
  const status = studentSkill?.verification_status || "UNVERIFIED";

  // Check Criteria Breakdown
  const supportingEvidence = evidenceList?.find(
    (e) =>
      (e.type === "CERTIFICATE" || e.type === "PROJECT_DOCUMENT") &&
      e.mapped_skills?.includes(skillName)
  );

  const repoEvidence = githubEvidence?.find(
    (e) => e.type === "GITHUB_REPO" && e.mapped_skills?.includes(skillName)
  );

  const assessAvailability = availableAssessments?.find(
    (a) => a.skill_id === skillId || a.skill_name === skillName
  );

  const isPracticalPassed =
    status === "SKILL_ASSESSED" || status === "SKILL_VERIFIED";
  const isFollowupPassed = status === "SKILL_VERIFIED";

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={isRefetching}
          onRefresh={refetchProfile}
          tintColor={colors.primary}
        />
      }
    >
      <TouchableOpacity
        style={styles.backRow}
        onPress={() => navigation.goBack()}
      >
        <ArrowLeft size={18} color={colors.textSecondary} />
        <Text style={styles.backText}>All Skills</Text>
      </TouchableOpacity>

      <Card style={styles.headerCard}>
        <View style={styles.headerTop}>
          <Text style={styles.title}>{skillName}</Text>
          <SkillStatusBadge status={status} />
        </View>
        <Text style={styles.headerDescription}>
          The ProofPath Verification Engine deterministically evaluates 4
          independent criteria to establish verified placement proficiency.
        </Text>
      </Card>

      <Text style={styles.sectionTitle}>Verification Criteria Checklist</Text>

      {/* Criterion 1: Supporting Evidence */}
      <Card style={styles.criterionCard}>
        <View style={styles.criterionHeader}>
          <View style={styles.criterionLeft}>
            {supportingEvidence ? (
              <CheckCircle2 size={22} color={colors.status.SKILL_VERIFIED.text} />
            ) : (
              <XCircle size={22} color={colors.textMuted} />
            )}
            <View style={{ marginLeft: 12 }}>
              <Text style={styles.criterionTitle}>
                1. Supporting Certificate / Document
              </Text>
              <Text style={styles.criterionSubtitle}>
                {supportingEvidence
                  ? `Verified via ${supportingEvidence.original_filename || "Document"}`
                  : "Certificate or project document required"}
              </Text>
            </View>
          </View>
          <FileCheck
            size={18}
            color={supportingEvidence ? colors.accent : colors.textMuted}
          />
        </View>

        {!supportingEvidence && (
          <Button
            title="Upload Supporting Certificate"
            onPress={() => navigation.navigate("Evidence")}
            variant="outline"
            size="small"
            style={styles.criterionActionBtn}
          />
        )}
      </Card>

      {/* Criterion 2: Practical Assessment */}
      <Card style={styles.criterionCard}>
        <View style={styles.criterionHeader}>
          <View style={styles.criterionLeft}>
            {isPracticalPassed ? (
              <CheckCircle2 size={22} color={colors.status.SKILL_VERIFIED.text} />
            ) : (
              <XCircle size={22} color={colors.textMuted} />
            )}
            <View style={{ marginLeft: 12 }}>
              <Text style={styles.criterionTitle}>
                2. Practical Skill Assessment
              </Text>
              <Text style={styles.criterionSubtitle}>
                {isPracticalPassed
                  ? "Completed with passing score (70%+)"
                  : assessAvailability?.practical_available
                  ? "Ready to take practical assessment"
                  : "Requires supporting evidence first"}
              </Text>
            </View>
          </View>
          <Award
            size={18}
            color={isPracticalPassed ? colors.accent : colors.textMuted}
          />
        </View>

        {!isPracticalPassed && assessAvailability?.practical_available && (
          <Button
            title="Start Practical Assessment"
            onPress={() =>
              navigation.navigate("AssessmentTake", {
                skillId,
                skillName,
                type: "PRACTICAL",
              })
            }
            size="small"
            style={styles.criterionActionBtn}
          />
        )}
      </Card>

      {/* Criterion 3: GitHub Project Evidence */}
      <Card style={styles.criterionCard}>
        <View style={styles.criterionHeader}>
          <View style={styles.criterionLeft}>
            {repoEvidence ? (
              <CheckCircle2 size={22} color={colors.status.SKILL_VERIFIED.text} />
            ) : (
              <XCircle size={22} color={colors.textMuted} />
            )}
            <View style={{ marginLeft: 12 }}>
              <Text style={styles.criterionTitle}>
                3. GitHub Project Evidence
              </Text>
              <Text style={styles.criterionSubtitle}>
                {repoEvidence
                  ? `Linked: ${repoEvidence.original_filename || "Repository"}`
                  : "Requires project repository mapped to skill"}
              </Text>
            </View>
          </View>
          <GitBranch
            size={18}
            color={repoEvidence ? colors.accent : colors.textMuted}
          />
        </View>

        {!repoEvidence && (
          <Button
            title="Connect & Select GitHub Project"
            onPress={() => navigation.navigate("GitHub")}
            variant="outline"
            size="small"
            style={styles.criterionActionBtn}
          />
        )}
      </Card>

      {/* Criterion 4: Follow-up Assessment */}
      <Card style={styles.criterionCard}>
        <View style={styles.criterionHeader}>
          <View style={styles.criterionLeft}>
            {isFollowupPassed ? (
              <CheckCircle2 size={22} color={colors.status.SKILL_VERIFIED.text} />
            ) : (
              <XCircle size={22} color={colors.textMuted} />
            )}
            <View style={{ marginLeft: 12 }}>
              <Text style={styles.criterionTitle}>
                4. Code Explanation Follow-up
              </Text>
              <Text style={styles.criterionSubtitle}>
                {isFollowupPassed
                  ? "Passed repository architectural check"
                  : assessAvailability?.followup_available
                  ? "Ready to take follow-up assessment"
                  : "Requires practical passed and GitHub repo linked"}
              </Text>
            </View>
          </View>
          <ShieldCheck
            size={18}
            color={isFollowupPassed ? colors.accent : colors.textMuted}
          />
        </View>

        {!isFollowupPassed && assessAvailability?.followup_available && (
          <Button
            title="Start Follow-up Assessment"
            onPress={() =>
              navigation.navigate("AssessmentTake", {
                skillId,
                skillName,
                type: "FOLLOW_UP",
              })
            }
            size="small"
            style={styles.criterionActionBtn}
          />
        )}
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
  backRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 14,
  },
  backText: {
    fontSize: 14,
    color: colors.textSecondary,
    marginLeft: 6,
  },
  headerCard: {
    padding: 18,
    marginBottom: 20,
  },
  headerTop: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  title: {
    fontSize: 22,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  headerDescription: {
    fontSize: 13,
    color: colors.textSecondary,
    lineHeight: 18,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: colors.textPrimary,
    marginBottom: 12,
  },
  criterionCard: {
    padding: 16,
    marginBottom: 12,
  },
  criterionHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  criterionLeft: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
  },
  criterionTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: colors.textPrimary,
  },
  criterionSubtitle: {
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 2,
  },
  criterionActionBtn: {
    marginTop: 14,
  },
});
