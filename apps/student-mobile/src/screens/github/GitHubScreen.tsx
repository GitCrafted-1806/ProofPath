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
import {
  fetchGitHubStatus,
  fetchGitHubEvidence,
  connectDemoGitHub,
  disconnectGitHub,
} from "../../api/github";
import { colors } from "../../theme/colors";
import { Card } from "../../components/common/Card";
import { Badge } from "../../components/common/Badge";
import { Button } from "../../components/common/Button";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import { ErrorBanner } from "../../components/common/ErrorBanner";
import { EmptyState } from "../../components/common/EmptyState";
import { RepoSelectModal } from "./RepoSelectModal";
import {
  GitBranch,
  FolderGit2,
  CheckCircle2,
  ExternalLink,
  Plus,
} from "lucide-react-native";

interface GitHubScreenProps {
  navigation: any;
}

export const GitHubScreen: React.FC<GitHubScreenProps> = ({ navigation }) => {
  const queryClient = useQueryClient();
  const [repoModalVisible, setRepoModalVisible] = useState(false);

  const {
    data: status,
    isLoading: isStatusLoading,
    error: statusError,
    refetch: refetchStatus,
    isRefetching,
  } = useQuery({
    queryKey: ["github-status"],
    queryFn: fetchGitHubStatus,
  });

  const {
    data: evidenceList,
    refetch: refetchEvidence,
  } = useQuery({
    queryKey: ["github-evidence"],
    queryFn: fetchGitHubEvidence,
  });

  const connectMutation = useMutation({
    mutationFn: connectDemoGitHub,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["github-status"] });
      queryClient.invalidateQueries({ queryKey: ["github-repos"] });
    },
    onError: (err: any) => {
      Alert.alert("Connection Error", err.message || "Failed to connect GitHub.");
    },
  });

  const disconnectMutation = useMutation({
    mutationFn: disconnectGitHub,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["github-status"] });
      queryClient.invalidateQueries({ queryKey: ["github-evidence"] });
      queryClient.invalidateQueries({ queryKey: ["profile"] });
    },
  });

  const handleDisconnect = () => {
    Alert.alert(
      "Disconnect GitHub",
      "Are you sure you want to disconnect your GitHub account? Any dependent verification statuses will update accordingly.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Disconnect",
          style: "destructive",
          onPress: () => disconnectMutation.mutate(),
        },
      ]
    );
  };

  const onRefresh = () => {
    refetchStatus();
    refetchEvidence();
  };

  if (isStatusLoading && !isRefetching) {
    return (
      <View style={styles.centerContainer}>
        <LoadingSpinner message="Checking GitHub status..." />
      </View>
    );
  }

  const isConnected = status?.is_connected;
  const projectList = evidenceList || [];

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
          <Text style={styles.title}>GitHub Project Evidence</Text>
          <Text style={styles.subtitle}>
            Link repository projects to prove implementation depth and unlock Skill Verified status.
          </Text>
        </View>

        {statusError && (
          <ErrorBanner
            message={(statusError as any).message || "Failed to load GitHub status."}
            onRetry={refetchStatus}
          />
        )}

        {/* GitHub Connection Card */}
        <Card style={styles.statusCard}>
          <View style={styles.statusHeader}>
            <View style={styles.githubIconContainer}>
              <FolderGit2 size={28} color={colors.accent} />
            </View>
            <View style={styles.statusMeta}>
              <Text style={styles.statusTitle}>
                {isConnected ? status.github_username : "GitHub Account"}
              </Text>
              <Text style={styles.statusSubtitle}>
                {isConnected
                  ? "Connected • Ready for repository selection"
                  : "Link your GitHub profile in DEMO_MODE"}
              </Text>
            </View>
            {isConnected && (
              <Badge
                label="Connected"
                textColor={colors.status.SKILL_VERIFIED.text}
                bgColor={colors.status.SKILL_VERIFIED.bg}
              />
            )}
          </View>

          {isConnected ? (
            <View style={styles.connectedActions}>
              <Button
                title="Select Repository as Project Evidence"
                onPress={() => setRepoModalVisible(true)}
                icon={<Plus size={16} color={colors.textWhite} />}
                style={styles.selectRepoBtn}
              />
              <Button
                title="Disconnect Account"
                onPress={handleDisconnect}
                variant="ghost"
                size="small"
                loading={disconnectMutation.isPending}
                style={styles.disconnectBtn}
              />
            </View>
          ) : (
            <Button
              title="Connect GitHub (Demo Mode)"
              onPress={() => connectMutation.mutate()}
              loading={connectMutation.isPending}
              icon={<GitBranch size={16} color={colors.textWhite} />}
              style={styles.connectBtn}
            />
          )}
        </Card>

        {/* Selected Projects Section */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Selected Project Evidence</Text>
          {isConnected && (
            <TouchableOpacity
              style={styles.addProjectRow}
              onPress={() => setRepoModalVisible(true)}
            >
              <Plus size={14} color={colors.primary} />
              <Text style={styles.addText}>Add Project</Text>
            </TouchableOpacity>
          )}
        </View>

        {projectList.length === 0 ? (
          <EmptyState
            icon={<FolderGit2 size={40} color={colors.primary} />}
            title="No GitHub Evidence Selected"
            description={
              isConnected
                ? "Select a repository to prove your implementation skills in Python, Pandas, Matplotlib, or Git."
                : "Connect your GitHub account above to select a repository."
            }
            actionTitle={isConnected ? "Select Repository" : "Connect GitHub"}
            onAction={
              isConnected
                ? () => setRepoModalVisible(true)
                : () => connectMutation.mutate()
            }
          />
        ) : (
          projectList.map((repo) => (
            <Card key={repo.id} style={styles.projectCard}>
              <View style={styles.projectHeader}>
                <View style={styles.projectLeft}>
                  <GitBranch size={20} color={colors.accent} />
                  <Text style={styles.projectName}>
                    {repo.original_filename || "Project Repository"}
                  </Text>
                </View>
                <Badge
                  label="Registered"
                  textColor={colors.status.SKILL_VERIFIED.text}
                  bgColor={colors.status.SKILL_VERIFIED.bg}
                />
              </View>

              {repo.extracted_metadata?.description && (
                <Text style={styles.projectDesc}>
                  {repo.extracted_metadata.description}
                </Text>
              )}

              <View style={styles.projectFooter}>
                <View style={styles.skillsRow}>
                  {repo.mapped_skills?.map((skill) => (
                    <Badge
                      key={skill}
                      label={skill}
                      textColor={colors.accent}
                      bgColor="rgba(6, 182, 212, 0.12)"
                      style={styles.skillTag}
                    />
                  ))}
                </View>
              </View>
            </Card>
          ))
        )}
      </ScrollView>

      <RepoSelectModal
        visible={repoModalVisible}
        onClose={() => setRepoModalVisible(false)}
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
  statusCard: {
    padding: 18,
    marginBottom: 20,
  },
  statusHeader: {
    flexDirection: "row",
    alignItems: "center",
  },
  githubIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: "#1E293B",
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },
  statusMeta: {
    flex: 1,
  },
  statusTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  statusSubtitle: {
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 2,
  },
  connectedActions: {
    marginTop: 16,
  },
  selectRepoBtn: {
    marginBottom: 8,
  },
  disconnectBtn: {
    alignSelf: "center",
  },
  connectBtn: {
    marginTop: 16,
  },
  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
    paddingHorizontal: 2,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: colors.textPrimary,
  },
  addProjectRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
  },
  addText: {
    fontSize: 13,
    color: colors.primary,
    fontWeight: "600",
  },
  projectCard: {
    padding: 16,
    marginBottom: 12,
  },
  projectHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  projectLeft: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
  },
  projectName: {
    fontSize: 15,
    fontWeight: "600",
    color: colors.textPrimary,
    marginLeft: 8,
  },
  projectDesc: {
    fontSize: 12,
    color: colors.textSecondary,
    marginBottom: 12,
    lineHeight: 16,
  },
  projectFooter: {
    borderTopWidth: 1,
    borderTopColor: "rgba(255,255,255,0.05)",
    paddingTop: 10,
  },
  skillsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
  },
  skillTag: {
    marginRight: 4,
  },
});
