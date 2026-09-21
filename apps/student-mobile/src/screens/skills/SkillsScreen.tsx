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
import { colors } from "../../theme/colors";
import { Card } from "../../components/common/Card";
import { SkillStatusBadge } from "../../components/skills/SkillStatusBadge";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import { ErrorBanner } from "../../components/common/ErrorBanner";
import { ChevronRight, ShieldCheck, ExternalLink } from "lucide-react-native";

interface SkillsScreenProps {
  navigation: any;
}

export const SkillsScreen: React.FC<SkillsScreenProps> = ({ navigation }) => {
  const {
    data: profile,
    isLoading,
    error,
    refetch,
    isRefetching,
  } = useQuery({
    queryKey: ["profile"],
    queryFn: fetchStudentProfile,
  });

  if (isLoading && !isRefetching) {
    return (
      <View style={styles.centerContainer}>
        <LoadingSpinner message="Fetching skills status..." />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centerContainer}>
        <ErrorBanner
          message={(error as any).message || "Failed to load skills."}
          onRetry={refetch}
        />
      </View>
    );
  }

  const skills = profile?.skills || [];

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={isRefetching}
          onRefresh={refetch}
          tintColor={colors.primary}
          colors={[colors.primary]}
        />
      }
    >
      <View style={styles.header}>
        <Text style={styles.title}>MVP Skills & Verification</Text>
        <Text style={styles.subtitle}>
          Deterministic proof-backed verification for technical placement readiness.
        </Text>
      </View>

      {/* Resume Verification Banner */}
      <TouchableOpacity
        activeOpacity={0.8}
        onPress={() => navigation.navigate("VerificationProfile")}
      >
        <Card style={styles.resumeCard}>
          <View style={styles.resumeLeft}>
            <ShieldCheck size={24} color={colors.accent} />
            <View style={{ marginLeft: 12 }}>
              <Text style={styles.resumeTitle}>Public Verification Profile</Text>
              <Text style={styles.resumeSubtitle}>
                Resume-ready portfolio link with cryptographic proofs
              </Text>
            </View>
          </View>
          <ExternalLink size={18} color={colors.accent} />
        </Card>
      </TouchableOpacity>

      {/* Skills List */}
      <View style={styles.skillsList}>
        {skills.map((skill) => (
          <TouchableOpacity
            key={skill.skill_id}
            activeOpacity={0.7}
            onPress={() =>
              navigation.navigate("SkillDetail", {
                skillId: skill.skill_id,
                skillName: skill.skill_name,
                status: skill.verification_status,
              })
            }
          >
            <Card style={styles.skillCard}>
              <View style={styles.cardTop}>
                <Text style={styles.skillName}>{skill.skill_name}</Text>
                <SkillStatusBadge status={skill.verification_status} />
              </View>

              <View style={styles.cardBottom}>
                <Text style={styles.updatedText}>
                  Status determined by backend engine
                </Text>
                <View style={styles.arrowRow}>
                  <Text style={styles.viewCriteriaText}>View Criteria</Text>
                  <ChevronRight size={16} color={colors.primary} />
                </View>
              </View>
            </Card>
          </TouchableOpacity>
        ))}
      </View>
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
  header: {
    marginBottom: 16,
  },
  title: {
    fontSize: 22,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  subtitle: {
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: 4,
    lineHeight: 18,
  },
  resumeCard: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 14,
    backgroundColor: "rgba(6, 182, 212, 0.08)",
    borderColor: "rgba(6, 182, 212, 0.3)",
    marginBottom: 16,
  },
  resumeLeft: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
  },
  resumeTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: colors.textPrimary,
  },
  resumeSubtitle: {
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 2,
  },
  skillsList: {
    gap: 4,
  },
  skillCard: {
    padding: 16,
  },
  cardTop: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  skillName: {
    fontSize: 18,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  cardBottom: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    borderTopWidth: 1,
    borderTopColor: "rgba(255,255,255,0.05)",
    paddingTop: 10,
  },
  updatedText: {
    fontSize: 11,
    color: colors.textMuted,
  },
  arrowRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  viewCriteriaText: {
    fontSize: 12,
    fontWeight: "600",
    color: colors.primary,
    marginRight: 2,
  },
});
