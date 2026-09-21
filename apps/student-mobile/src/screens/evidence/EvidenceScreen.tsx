import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  Alert,
} from "react-native";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchMyEvidence, deleteEvidence } from "../../api/evidence";
import { colors } from "../../theme/colors";
import { Card } from "../../components/common/Card";
import { Badge } from "../../components/common/Badge";
import { Button } from "../../components/common/Button";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import { ErrorBanner } from "../../components/common/ErrorBanner";
import { EmptyState } from "../../components/common/EmptyState";
import { EvidenceUploadModal } from "./EvidenceUploadModal";
import {
  FileText,
  Upload,
  Trash2,
  CheckCircle,
  FileCheck2,
} from "lucide-react-native";

interface EvidenceScreenProps {
  navigation: any;
}

export const EvidenceScreen: React.FC<EvidenceScreenProps> = ({ navigation }) => {
  const queryClient = useQueryClient();
  const [uploadModalVisible, setUploadModalVisible] = useState(false);

  const {
    data: evidenceList,
    isLoading,
    error,
    refetch,
    isRefetching,
  } = useQuery({
    queryKey: ["evidence"],
    queryFn: fetchMyEvidence,
  });

  const deleteMutation = useMutation({
    mutationFn: deleteEvidence,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["evidence"] });
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["assessments-available"] });
    },
    onError: (err: any) => {
      Alert.alert("Delete Error", err.message || "Failed to delete evidence.");
    },
  });

  const handleDelete = (evidenceId: string, filename: string) => {
    Alert.alert(
      "Delete Evidence",
      `Are you sure you want to delete "${filename}"? Any dependent verification states will be re-evaluated.`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: () => deleteMutation.mutate(evidenceId),
        },
      ]
    );
  };

  if (isLoading && !isRefetching) {
    return (
      <View style={styles.centerContainer}>
        <LoadingSpinner message="Loading your submitted evidence..." />
      </View>
    );
  }

  const list = evidenceList || [];

  return (
    <View style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl
            refreshing={isRefetching}
            onRefresh={refetch}
            tintColor={colors.primary}
          />
        }
      >
        <View style={styles.header}>
          <View>
            <Text style={styles.title}>Document & Certificate Evidence</Text>
            <Text style={styles.subtitle}>
              Upload certificates or reports to unlock practical skill assessments.
            </Text>
          </View>
        </View>

        <Button
          title="Upload New Evidence"
          onPress={() => setUploadModalVisible(true)}
          icon={<Upload size={18} color={colors.textWhite} />}
          style={styles.uploadBtn}
        />

        {error && (
          <ErrorBanner
            message={(error as any).message || "Failed to load evidence records."}
            onRetry={refetch}
          />
        )}

        {list.length === 0 ? (
          <EmptyState
            icon={<FileCheck2 size={44} color={colors.primary} />}
            title="No Evidence Uploaded Yet"
            description="Upload certificates from Coursera, NPTEL, Udemy, or college project reports to support your MVP skills."
            actionTitle="Upload First Document"
            onAction={() => setUploadModalVisible(true)}
          />
        ) : (
          list.map((ev) => {
            const authCfg =
              colors.authenticity[ev.authenticity_state as keyof typeof colors.authenticity] ||
              colors.authenticity.SUBMITTED;

            return (
              <Card key={ev.id} style={styles.evidenceCard}>
                <View style={styles.cardHeader}>
                  <View style={styles.headerLeft}>
                    <FileText size={22} color={colors.primary} />
                    <View style={{ marginLeft: 10, flex: 1 }}>
                      <Text style={styles.fileName} numberOfLines={1}>
                        {ev.original_filename || "Evidence Document"}
                      </Text>
                      <Text style={styles.fileType}>{ev.type}</Text>
                    </View>
                  </View>

                  <Badge
                    label={ev.authenticity_state.replace("_", " ")}
                    textColor={authCfg.text}
                    bgColor={authCfg.bg}
                  />
                </View>

                {/* Extracted Metadata Summary */}
                {ev.extracted_metadata && (
                  <View style={styles.metadataBox}>
                    {ev.extracted_metadata.issuer && (
                      <Text style={styles.metadataText}>
                        Issuer:{" "}
                        <Text style={{ color: colors.textPrimary }}>
                          {ev.extracted_metadata.issuer}
                        </Text>
                      </Text>
                    )}
                    {ev.extracted_metadata.course_name && (
                      <Text style={styles.metadataText}>
                        Course:{" "}
                        <Text style={{ color: colors.textPrimary }}>
                          {ev.extracted_metadata.course_name}
                        </Text>
                      </Text>
                    )}
                  </View>
                )}

                {/* Mapped Skills */}
                <View style={styles.cardFooter}>
                  <View style={styles.skillsRow}>
                    {ev.mapped_skills && ev.mapped_skills.length > 0 ? (
                      ev.mapped_skills.map((skillName) => (
                        <Badge
                          key={skillName}
                          label={skillName}
                          textColor={colors.accent}
                          bgColor="rgba(6, 182, 212, 0.12)"
                          style={styles.skillTag}
                        />
                      ))
                    ) : (
                      <Text style={styles.noSkillsText}>No skills detected</Text>
                    )}
                  </View>

                  {/* Delete Option */}
                  {ev.authenticity_state !== "INSTITUTION_VERIFIED" && (
                    <TouchableOpacity
                      style={styles.deleteButton}
                      onPress={() =>
                        handleDelete(ev.id, ev.original_filename || "Evidence")
                      }
                    >
                      <Trash2 size={16} color={colors.error} />
                    </TouchableOpacity>
                  )}
                </View>
              </Card>
            );
          })
        )}
      </ScrollView>

      <EvidenceUploadModal
        visible={uploadModalVisible}
        onClose={() => setUploadModalVisible(false)}
      />
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
  centerContainer: {
    flex: 1,
    backgroundColor: colors.bgDark,
    alignItems: "center",
    justifyContent: "center",
    padding: 20,
  },
  header: {
    marginBottom: 14,
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
  uploadBtn: {
    marginBottom: 16,
  },
  evidenceCard: {
    padding: 16,
    marginBottom: 12,
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
  },
  headerLeft: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
    marginRight: 10,
  },
  fileName: {
    fontSize: 15,
    fontWeight: "600",
    color: colors.textPrimary,
  },
  fileType: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 2,
  },
  metadataBox: {
    backgroundColor: colors.cardElevated,
    borderRadius: 8,
    padding: 10,
    marginBottom: 10,
  },
  metadataText: {
    fontSize: 12,
    color: colors.textSecondary,
    marginBottom: 2,
  },
  cardFooter: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    borderTopWidth: 1,
    borderTopColor: "rgba(255,255,255,0.05)",
    paddingTop: 10,
  },
  skillsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
    flex: 1,
  },
  skillTag: {
    marginRight: 4,
  },
  noSkillsText: {
    fontSize: 12,
    color: colors.textMuted,
  },
  deleteButton: {
    padding: 6,
    borderRadius: 6,
    backgroundColor: "rgba(239, 68, 68, 0.1)",
  },
});
