import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from "react-native";
import { useQueryClient } from "@tanstack/react-query";
import { startAssessment, submitAssessment } from "../../api/assessments";
import { AssessmentTakeResponse, AssessmentQuestionClient } from "../../types";
import { colors } from "../../theme/colors";
import { Card } from "../../components/common/Card";
import { Button } from "../../components/common/Button";
import { Input } from "../../components/common/Input";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import { ErrorBanner } from "../../components/common/ErrorBanner";
import { CheckCircle2, Circle, ArrowLeft, ArrowRight, Send } from "lucide-react-native";

interface AssessmentTakeScreenProps {
  route: any;
  navigation: any;
}

export const AssessmentTakeScreen: React.FC<AssessmentTakeScreenProps> = ({
  route,
  navigation,
}) => {
  const { skillId, skillName, type } = route.params;
  const queryClient = useQueryClient();

  const [assessment, setAssessment] = useState<AssessmentTakeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const initAssessment = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await startAssessment(skillId, type);
        setAssessment(data);
      } catch (err: any) {
        setError(err.message || "Failed to initiate assessment.");
      } finally {
        setLoading(false);
      }
    };

    initAssessment();
  }, [skillId, type]);

  const handleAnswerSelect = (questionId: string, answer: any) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: answer,
    }));
  };

  const handleSubmit = async () => {
    if (!assessment) return;

    // Check if any question remains unanswered
    const questionsCount = assessment.questions.length;
    const answeredCount = Object.keys(answers).length;

    if (answeredCount < questionsCount) {
      Alert.alert(
        "Incomplete Submission",
        `You have answered ${answeredCount} of ${questionsCount} questions. Do you want to submit anyway?`,
        [
          { text: "Review", style: "cancel" },
          {
            text: "Submit Now",
            onPress: executeSubmit,
          },
        ]
      );
    } else {
      executeSubmit();
    }
  };

  const executeSubmit = async () => {
    if (!assessment) return;
    try {
      setSubmitting(true);
      setError(null);
      const result = await submitAssessment(assessment.id, answers);

      // Invalidate relevant React Query caches
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["assessments-available"] });
      queryClient.invalidateQueries({ queryKey: ["assessments-history"] });

      // Navigate to results
      navigation.replace("AssessmentResult", { result });
    } catch (err: any) {
      setError(err.message || "Submission failed. Please try again.");
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <LoadingSpinner message={`Starting ${type} Assessment for ${skillName}...`} />
      </View>
    );
  }

  if (error && !assessment) {
    return (
      <View style={styles.centerContainer}>
        <ErrorBanner message={error} onRetry={() => navigation.goBack()} />
        <Button title="Back to Skills" onPress={() => navigation.goBack()} variant="outline" />
      </View>
    );
  }

  const questions = assessment?.questions || [];
  const currentQuestion: AssessmentQuestionClient | undefined = questions[currentIdx];
  const isLastQuestion = currentIdx === questions.length - 1;

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      style={styles.container}
    >
      <ScrollView contentContainerStyle={styles.content}>
        {/* Top Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.cancelRow}>
            <ArrowLeft size={16} color={colors.textSecondary} />
            <Text style={styles.cancelText}>Cancel</Text>
          </TouchableOpacity>
          <Text style={styles.skillTitle}>
            {skillName} • {type}
          </Text>
          <Text style={styles.questionCounter}>
            Question {currentIdx + 1} of {questions.length}
          </Text>
        </View>

        {/* Progress Bar */}
        <View style={styles.progressBarBg}>
          <View
            style={[
              styles.progressBarFill,
              { width: `${((currentIdx + 1) / questions.length) * 100}%` },
            ]}
          />
        </View>

        {error && <ErrorBanner message={error} />}

        {currentQuestion && (
          <Card style={styles.questionCard}>
            <Text style={styles.questionText}>{currentQuestion.question}</Text>

            {/* Code Snippet Box if present */}
            {currentQuestion.code_snippet && (
              <View style={styles.codeSnippetBox}>
                <Text style={styles.codeText}>{currentQuestion.code_snippet}</Text>
              </View>
            )}

            {/* Answer Options according to type */}
            {currentQuestion.type === "MULTIPLE_CHOICE" && currentQuestion.options && (
              <View style={styles.optionsList}>
                {currentQuestion.options.map((option, optIdx) => {
                  const isSelected = answers[currentQuestion.id] === option;
                  return (
                    <TouchableOpacity
                      key={optIdx}
                      style={[
                        styles.optionRow,
                        isSelected && styles.optionRowSelected,
                      ]}
                      onPress={() => handleAnswerSelect(currentQuestion.id, option)}
                      activeOpacity={0.8}
                    >
                      {isSelected ? (
                        <CheckCircle2 size={18} color={colors.primary} />
                      ) : (
                        <Circle size={18} color={colors.borderHighlight} />
                      )}
                      <Text
                        style={[
                          styles.optionText,
                          isSelected && styles.optionTextSelected,
                        ]}
                      >
                        {option}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
            )}

            {currentQuestion.type === "CODE_OUTPUT" && (
              <View style={styles.inputAnswerBox}>
                <Input
                  label="Enter exact stdout output:"
                  placeholder="e.g. [2, 6, 10]"
                  value={answers[currentQuestion.id] || ""}
                  onChangeText={(val) => handleAnswerSelect(currentQuestion.id, val)}
                  autoCapitalize="none"
                />
              </View>
            )}

            {currentQuestion.type === "NUMERICAL_INPUT" && (
              <View style={styles.inputAnswerBox}>
                <Input
                  label="Enter numerical value:"
                  placeholder="e.g. 4"
                  value={answers[currentQuestion.id] || ""}
                  onChangeText={(val) => handleAnswerSelect(currentQuestion.id, val)}
                  keyboardType="numeric"
                />
              </View>
            )}
          </Card>
        )}

        {/* Navigation Footer */}
        <View style={styles.navRow}>
          <Button
            title="Previous"
            variant="outline"
            size="small"
            disabled={currentIdx === 0}
            onPress={() => setCurrentIdx((prev) => Math.max(0, prev - 1))}
          />

          {isLastQuestion ? (
            <Button
              title="Submit Assessment"
              onPress={handleSubmit}
              loading={submitting}
              icon={<Send size={16} color={colors.textWhite} />}
            />
          ) : (
            <Button
              title="Next Question"
              onPress={() => setCurrentIdx((prev) => Math.min(questions.length - 1, prev + 1))}
              icon={<ArrowRight size={16} color={colors.textWhite} />}
            />
          )}
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bgDark,
  },
  content: {
    padding: 18,
    paddingBottom: 40,
  },
  centerContainer: {
    flex: 1,
    backgroundColor: colors.bgDark,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
  },
  header: {
    marginBottom: 12,
  },
  cancelRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 10,
  },
  cancelText: {
    fontSize: 13,
    color: colors.textSecondary,
    marginLeft: 4,
  },
  skillTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  questionCounter: {
    fontSize: 13,
    color: colors.textMuted,
    marginTop: 2,
  },
  progressBarBg: {
    height: 4,
    backgroundColor: "rgba(255,255,255,0.08)",
    borderRadius: 2,
    marginBottom: 18,
  },
  progressBarFill: {
    height: "100%",
    backgroundColor: colors.primary,
    borderRadius: 2,
  },
  questionCard: {
    padding: 20,
    marginBottom: 20,
  },
  questionText: {
    fontSize: 16,
    fontWeight: "600",
    color: colors.textPrimary,
    lineHeight: 22,
    marginBottom: 16,
  },
  codeSnippetBox: {
    backgroundColor: "#060A10",
    borderRadius: 8,
    padding: 14,
    borderWidth: 1,
    borderColor: "#1E293B",
    marginBottom: 18,
  },
  codeText: {
    fontFamily: Platform.OS === "ios" ? "Courier" : "monospace",
    fontSize: 13,
    color: "#38BDF8",
    lineHeight: 18,
  },
  optionsList: {
    gap: 10,
  },
  optionRow: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.cardElevated,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: colors.borderDark,
    padding: 14,
  },
  optionRowSelected: {
    borderColor: colors.primary,
    backgroundColor: "rgba(124, 58, 237, 0.12)",
  },
  optionText: {
    fontSize: 14,
    color: colors.textSecondary,
    marginLeft: 10,
    flex: 1,
  },
  optionTextSelected: {
    color: colors.textPrimary,
    fontWeight: "600",
  },
  inputAnswerBox: {
    marginTop: 6,
  },
  navRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
});
