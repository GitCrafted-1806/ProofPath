import React from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from "react-native";
import { AssessmentResultResponse } from "../../types";
import { colors } from "../../theme/colors";
import { Card } from "../../components/common/Card";
import { Button } from "../../components/common/Button";
import { SkillStatusBadge } from "../../components/skills/SkillStatusBadge";
import {
  CheckCircle2,
  XCircle,
  Award,
  ArrowRight,
  ShieldCheck,
} from "lucide-react-native";

interface AssessmentResultScreenProps {
  route: any;
  navigation: any;
}

export const AssessmentResultScreen: React.FC<AssessmentResultScreenProps> = ({
  route,
  navigation,
}) => {
  const result: AssessmentResultResponse = route.params.result;
  const isPassed = result.passed;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Result Hero Header */}
      <Card
        style={[
          styles.heroCard,
          {
            borderColor: isPassed
              ? colors.status.SKILL_VERIFIED.border
              : colors.error,
          },
        ]}
      >
        <View style={styles.heroIconContainer}>
          {isPassed ? (
            <CheckCircle2 size={48} color={colors.status.SKILL_VERIFIED.text} />
          ) : (
            <XCircle size={48} color={colors.error} />
          )}
        </View>

        <Text style={styles.heroTitle}>
          {isPassed ? "Assessment Passed" : "Assessment Not Passed"}
        </Text>
        <Text style={styles.heroSubtitle}>
          {result.skill_name} • {result.type} Assessment
        </Text>

        <View style={styles.scoreRow}>
          <Text style={styles.scoreLabel}>Score Earned:</Text>
          <Text
            style={[
              styles.scoreNumber,
              {
                color: isPassed
                  ? colors.status.SKILL_VERIFIED.text
                  : colors.error,
              },
            ]}
          >
            {result.score?.toFixed(1)}%
          </Text>
        </View>

        <Text style={styles.summaryText}>{result.evaluation_summary}</Text>

        <View style={styles.newStatusBox}>
          <Text style={styles.newStatusLabel}>Updated Skill Status:</Text>
          <SkillStatusBadge status={result.new_skill_status} />
        </View>
      </Card>

      {/* Question Feedback Breakdown */}
      <Text style={styles.sectionTitle}>Question-by-Question Review</Text>

      {result.feedback && result.feedback.length > 0 ? (
        result.feedback.map((item, idx) => (
          <Card key={item.question_id || idx} style={styles.feedbackCard}>
            <View style={styles.feedbackHeader}>
              <View style={{ flex: 1, marginRight: 8 }}>
                <Text style={styles.questionIndex}>Question {idx + 1}</Text>
                <Text style={styles.feedbackQuestion}>{item.question}</Text>
              </View>
              {item.is_correct ? (
                <CheckCircle2
                  size={20}
                  color={colors.status.SKILL_VERIFIED.text}
                />
              ) : (
                <XCircle size={20} color={colors.error} />
              )}
            </View>

            <View style={styles.answerComparisonBox}>
              <Text style={styles.answerText}>
                Your Answer:{" "}
                <Text
                  style={{
                    color: item.is_correct
                      ? colors.status.SKILL_VERIFIED.text
                      : colors.error,
                    fontWeight: "600",
                  }}
                >
                  {item.submitted_answer !== null &&
                  item.submitted_answer !== undefined
                    ? String(item.submitted_answer)
                    : "Unanswered"}
                </Text>
              </Text>

              {!item.is_correct && (
                <Text style={styles.correctAnswerText}>
                  Correct Answer:{" "}
                  <Text style={{ color: colors.status.SKILL_VERIFIED.text, fontWeight: "600" }}>
                    {String(item.correct_answer)}
                  </Text>
                </Text>
              )}
            </View>

            {item.explanation && (
              <View style={styles.explanationBox}>
                <Text style={styles.explanationTitle}>Explanation</Text>
                <Text style={styles.explanationContent}>{item.explanation}</Text>
              </View>
            )}
          </Card>
        ))
      ) : null}

      {/* Action Buttons */}
      <View style={styles.actionButtons}>
        <Button
          title="View Skills Portfolio"
          onPress={() => navigation.navigate("Skills")}
          style={{ marginBottom: 10 }}
        />
        <Button
          title="Return to Dashboard"
          variant="outline"
          onPress={() => navigation.navigate("Dashboard")}
        />
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
    paddingBottom: 40,
  },
  heroCard: {
    alignItems: "center",
    padding: 24,
    marginBottom: 20,
    borderWidth: 1.5,
  },
  heroIconContainer: {
    marginBottom: 12,
  },
  heroTitle: {
    fontSize: 22,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  heroSubtitle: {
    fontSize: 14,
    color: colors.textSecondary,
    marginTop: 2,
    marginBottom: 14,
  },
  scoreRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 10,
    gap: 8,
  },
  scoreLabel: {
    fontSize: 16,
    color: colors.textSecondary,
  },
  scoreNumber: {
    fontSize: 24,
    fontWeight: "800",
  },
  summaryText: {
    fontSize: 13,
    color: colors.textSecondary,
    textAlign: "center",
    marginBottom: 16,
    lineHeight: 18,
  },
  newStatusBox: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.cardElevated,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 10,
    gap: 10,
  },
  newStatusLabel: {
    fontSize: 13,
    color: colors.textSecondary,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: colors.textPrimary,
    marginBottom: 12,
  },
  feedbackCard: {
    padding: 16,
    marginBottom: 12,
  },
  feedbackHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 10,
  },
  questionIndex: {
    fontSize: 11,
    color: colors.textMuted,
    fontWeight: "700",
    textTransform: "uppercase",
  },
  feedbackQuestion: {
    fontSize: 14,
    fontWeight: "600",
    color: colors.textPrimary,
    marginTop: 2,
    lineHeight: 18,
  },
  answerComparisonBox: {
    backgroundColor: colors.cardElevated,
    padding: 10,
    borderRadius: 8,
    marginBottom: 8,
  },
  answerText: {
    fontSize: 13,
    color: colors.textSecondary,
  },
  correctAnswerText: {
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: 4,
  },
  explanationBox: {
    backgroundColor: "rgba(124, 58, 237, 0.08)",
    borderColor: "rgba(124, 58, 237, 0.2)",
    borderWidth: 1,
    borderRadius: 8,
    padding: 10,
    marginTop: 4,
  },
  explanationTitle: {
    fontSize: 11,
    fontWeight: "700",
    color: colors.primary,
    marginBottom: 2,
    textTransform: "uppercase",
  },
  explanationContent: {
    fontSize: 12,
    color: colors.textSecondary,
    lineHeight: 16,
  },
  actionButtons: {
    marginTop: 10,
  },
});
