import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
} from "react-native";
import { useQuery } from "@tanstack/react-query";
import {
  fetchAvailableAssessments,
  fetchAssessmentHistory,
} from "../../api/assessments";
import { colors } from "../../theme/colors";
import { Card } from "../../components/common/Card";
import { Badge } from "../../components/common/Badge";
import { Button } from "../../components/common/Button";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import { ErrorBanner } from "../../components/common/ErrorBanner";
import { EmptyState } from "../../components/common/EmptyState";
import {
  Award,
  PlayCircle,
  Clock,
  CheckCircle2,
  XCircle,
  HelpCircle,
} from "lucide-react-native";

interface AssessmentsListScreenProps {
  navigation: any;
}

export const AssessmentsListScreen: React.FC<AssessmentsListScreenProps> = ({
  navigation,
}) => {
  const [activeTab, setActiveTab] = useState<"AVAILABLE" | "HISTORY">("AVAILABLE");

  const {
    data: availableList,
    isLoading: isAvailableLoading,
    error: availableError,
    refetch: refetchAvailable,
    isRefetching: isAvailableRefetching,
  } = useQuery({
    queryKey: ["assessments-available"],
    queryFn: fetchAvailableAssessments,
  });

  const {
    data: historyList,
    isLoading: isHistoryLoading,
    error: historyError,
    refetch: refetchHistory,
    isRefetching: isHistoryRefetching,
  } = useQuery({
    queryKey: ["assessments-history"],
    queryFn: fetchAssessmentHistory,
  });

  const onRefresh = () => {
    refetchAvailable();
    refetchHistory();
  };

  const isRefetching = isAvailableRefetching || isHistoryRefetching;

  return (
    <View style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl
            refreshing={isRefetching}
            onRefresh={onRefresh}
            tintColor={colors.primary}
          />
        }
      >
        <View style={styles.header}>
          <Text style={styles.title}>Skill Assessments</Text>
          <Text style={styles.subtitle}>
            Deterministic testing evaluated by the backend verification engine (70% passing score).
          </Text>
        </View>

        {/* Tab Switcher */}
        <View style={styles.tabContainer}>
          <TouchableOpacity
            style={[
              styles.tabButton,
              activeTab === "AVAILABLE" && styles.tabButtonActive,
            ]}
            onPress={() => setActiveTab("AVAILABLE")}
          >
            <Text
              style={[
                styles.tabText,
                activeTab === "AVAILABLE" && styles.tabTextActive,
              ]}
            >
              Available Assessments
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.tabButton,
              activeTab === "HISTORY" && styles.tabButtonActive,
            ]}
            onPress={() => setActiveTab("HISTORY")}
          >
            <Text
              style={[
                styles.tabText,
                activeTab === "HISTORY" && styles.tabTextActive,
              ]}
            >
              History ({historyList?.length || 0})
            </Text>
          </TouchableOpacity>
        </View>

        {activeTab === "AVAILABLE" ? (
          <View>
            {isAvailableLoading && !isRefetching ? (
              <LoadingSpinner message="Checking assessment prerequisites..." />
            ) : availableError ? (
              <ErrorBanner
                message={(availableError as any).message || "Failed to load available assessments."}
                onRetry={refetchAvailable}
              />
            ) : availableList && availableList.length > 0 ? (
              availableList.map((item) => {
                const canStart = item.practical_available || item.followup_available;
                const assessType = item.practical_available ? "PRACTICAL" : "FOLLOW_UP";

                return (
                  <Card key={item.skill_id} style={styles.assessCard}>
                    <View style={styles.cardHeader}>
                      <Text style={styles.skillName}>{item.skill_name}</Text>
                      {canStart ? (
                        <Badge
                          label={
                            item.practical_available
                              ? "Practical Ready"
                              : "Follow-Up Ready"
                          }
                          textColor={colors.status.SKILL_ASSESSED.text}
                          bgColor={colors.status.SKILL_ASSESSED.bg}
                        />
                      ) : (
                        <Badge
                          label={item.current_status.replace("_", " ")}
                          textColor={colors.textMuted}
                          bgColor="rgba(255,255,255,0.06)"
                        />
                      )}
                    </View>

                    <Text style={styles.reasonText}>
                      {item.reason || "Assessment status evaluated."}
                    </Text>

                    {canStart && (
                      <Button
                        title={`Start ${
                          item.practical_available ? "Practical" : "Follow-Up"
                        } Assessment`}
                        onPress={() =>
                          navigation.navigate("AssessmentTake", {
                            skillId: item.skill_id,
                            skillName: item.skill_name,
                            type: assessType,
                          })
                        }
                        icon={<PlayCircle size={16} color={colors.textWhite} />}
                        style={styles.startBtn}
                      />
                    )}
                  </Card>
                );
              })
            ) : (
              <EmptyState
                icon={<Award size={40} color={colors.primary} />}
                title="No Assessments Available"
                description="Upload certificates or select GitHub project evidence to unlock skills assessments."
              />
            )}
          </View>
        ) : (
          <View>
            {isHistoryLoading && !isRefetching ? (
              <LoadingSpinner message="Loading assessment history..." />
            ) : historyError ? (
              <ErrorBanner
                message={(historyError as any).message || "Failed to load history."}
                onRetry={refetchHistory}
              />
            ) : historyList && historyList.length > 0 ? (
              historyList.map((hist) => (
                <Card key={hist.id} style={styles.historyCard}>
                  <View style={styles.cardHeader}>
                    <View style={styles.historyLeft}>
                      {hist.passed ? (
                        <CheckCircle2
                          size={20}
                          color={colors.status.SKILL_VERIFIED.text}
                        />
                      ) : (
                        <XCircle size={20} color={colors.error} />
                      )}
                      <View style={{ marginLeft: 10 }}>
                        <Text style={styles.historySkill}>
                          {hist.skill_name} ({hist.type})
                        </Text>
                        <Text style={styles.historyDate}>
                          {hist.completed_at
                            ? new Date(hist.completed_at).toLocaleDateString()
                            : "Completed"}
                        </Text>
                      </View>
                    </View>

                    <View style={styles.scorePill}>
                      <Text
                        style={[
                          styles.scoreText,
                          {
                            color: hist.passed
                              ? colors.status.SKILL_VERIFIED.text
                              : colors.error,
                          },
                        ]}
                      >
                        {hist.score !== null ? `${hist.score}%` : "Submitted"}
                      </Text>
                    </View>
                  </View>

                  {hist.evaluation_summary && (
                    <Text style={styles.summaryText}>{hist.evaluation_summary}</Text>
                  )}
                </Card>
              ))
            ) : (
              <EmptyState
                icon={<Clock size={40} color={colors.textMuted} />}
                title="No History Yet"
                description="Completed practical and follow-up assessments will appear here."
              />
            )}
          </View>
        )}
      </ScrollView>
    </View>
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
  tabContainer: {
    flexDirection: "row",
    backgroundColor: colors.cardDark,
    borderRadius: 10,
    padding: 4,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: colors.borderDark,
  },
  tabButton: {
    flex: 1,
    paddingVertical: 10,
    alignItems: "center",
    borderRadius: 8,
  },
  tabButtonActive: {
    backgroundColor: colors.cardElevated,
    borderColor: colors.borderHighlight,
    borderWidth: 1,
  },
  tabText: {
    fontSize: 13,
    fontWeight: "500",
    color: colors.textMuted,
  },
  tabTextActive: {
    color: colors.textPrimary,
    fontWeight: "700",
  },
  assessCard: {
    padding: 16,
    marginBottom: 12,
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  skillName: {
    fontSize: 16,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  reasonText: {
    fontSize: 13,
    color: colors.textSecondary,
    lineHeight: 18,
    marginBottom: 12,
  },
  startBtn: {
    marginTop: 4,
  },
  historyCard: {
    padding: 14,
    marginBottom: 10,
  },
  historyLeft: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
  },
  historySkill: {
    fontSize: 15,
    fontWeight: "600",
    color: colors.textPrimary,
  },
  historyDate: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 2,
  },
  scorePill: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
    backgroundColor: "rgba(255,255,255,0.06)",
  },
  scoreText: {
    fontSize: 13,
    fontWeight: "700",
  },
  summaryText: {
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 8,
    lineHeight: 16,
  },
});
