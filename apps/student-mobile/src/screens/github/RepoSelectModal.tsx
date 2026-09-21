import React from "react";
import {
  View,
  Text,
  StyleSheet,
  Modal,
  ScrollView,
  TouchableOpacity,
} from "react-native";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchGitHubRepositories, selectGitHubRepository } from "../../api/github";
import { colors } from "../../theme/colors";
import { Card } from "../../components/common/Card";
import { Badge } from "../../components/common/Badge";
import { Button } from "../../components/common/Button";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import { ErrorBanner } from "../../components/common/ErrorBanner";
import { GitBranch, Star, X, Check } from "lucide-react-native";

interface RepoSelectModalProps {
  visible: boolean;
  onClose: () => void;
}

export const RepoSelectModal: React.FC<RepoSelectModalProps> = ({
  visible,
  onClose,
}) => {
  const queryClient = useQueryClient();

  const {
    data: repositories,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["github-repos"],
    queryFn: fetchGitHubRepositories,
    enabled: visible,
  });

  const selectMutation = useMutation({
    mutationFn: selectGitHubRepository,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["github-evidence"] });
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["assessments-available"] });
      onClose();
    },
  });

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <View style={styles.modalOverlay}>
        <Card style={styles.modalCard}>
          <View style={styles.modalHeader}>
            <View>
              <Text style={styles.modalTitle}>Select Project Repository</Text>
              <Text style={styles.modalSubtitle}>
                Repositories are analyzed to map real project skills
              </Text>
            </View>
            <TouchableOpacity onPress={onClose}>
              <X size={22} color={colors.textSecondary} />
            </TouchableOpacity>
          </View>

          {isLoading ? (
            <LoadingSpinner message="Fetching repositories from GitHub..." />
          ) : error ? (
            <ErrorBanner
              message={(error as any).message || "Failed to load repositories."}
              onRetry={refetch}
            />
          ) : (
            <ScrollView style={styles.repoList}>
              {repositories && repositories.length > 0 ? (
                repositories.map((repo) => (
                  <TouchableOpacity
                    key={repo.full_name}
                    style={styles.repoCard}
                    activeOpacity={0.8}
                    disabled={selectMutation.isPending}
                    onPress={() => selectMutation.mutate(repo.full_name)}
                  >
                    <View style={styles.repoHeader}>
                      <GitBranch size={18} color={colors.accent} />
                      <Text style={styles.repoName}>{repo.name}</Text>
                    </View>

                    {repo.description && (
                      <Text style={styles.repoDesc} numberOfLines={2}>
                        {repo.description}
                      </Text>
                    )}

                    <View style={styles.repoMeta}>
                      {repo.language && (
                        <Badge
                          label={repo.language}
                          textColor={colors.primary}
                          bgColor="rgba(124, 58, 237, 0.12)"
                        />
                      )}
                      <View style={styles.starRow}>
                        <Star size={13} color={colors.warning} />
                        <Text style={styles.starText}>{repo.stars}</Text>
                      </View>
                      <Button
                        title="Select"
                        onPress={() => selectMutation.mutate(repo.full_name)}
                        size="small"
                        loading={
                          selectMutation.isPending &&
                          selectMutation.variables === repo.full_name
                        }
                        style={styles.selectBtn}
                      />
                    </View>
                  </TouchableOpacity>
                ))
              ) : (
                <Text style={styles.emptyText}>No repositories found.</Text>
              )}
            </ScrollView>
          )}
        </Card>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.75)",
    justifyContent: "flex-end",
  },
  modalCard: {
    backgroundColor: colors.cardElevated,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 22,
    maxHeight: "80%",
    borderColor: colors.borderHighlight,
    marginBottom: 0,
  },
  modalHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  modalSubtitle: {
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 2,
  },
  repoList: {
    maxHeight: 400,
  },
  repoCard: {
    backgroundColor: colors.cardDark,
    borderColor: colors.borderDark,
    borderWidth: 1,
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
  },
  repoHeader: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 6,
  },
  repoName: {
    fontSize: 15,
    fontWeight: "600",
    color: colors.textPrimary,
    marginLeft: 8,
  },
  repoDesc: {
    fontSize: 12,
    color: colors.textSecondary,
    marginBottom: 10,
    lineHeight: 16,
  },
  repoMeta: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  starRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
  },
  starText: {
    fontSize: 12,
    color: colors.textMuted,
  },
  selectBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  emptyText: {
    fontSize: 13,
    color: colors.textMuted,
    textAlign: "center",
    padding: 20,
  },
});
