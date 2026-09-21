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
import { useQuery } from "@tanstack/react-query";
import { fetchStudentProfile } from "../../api/students";
import { useAuth } from "../../context/AuthContext";
import { colors } from "../../theme/colors";
import { Card } from "../../components/common/Card";
import { Button } from "../../components/common/Button";
import { Input } from "../../components/common/Input";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import { ErrorBanner } from "../../components/common/ErrorBanner";
import { EditProfileModal } from "./EditProfileModal";
import { getApiBaseUrl, setApiBaseUrl } from "../../api/config";
import {
  User,
  GraduationCap,
  Building,
  Calendar,
  Award,
  Globe,
  LogOut,
  Edit3,
  Server,
  ExternalLink,
} from "lucide-react-native";

interface ProfileScreenProps {
  navigation: any;
}

export const ProfileScreen: React.FC<ProfileScreenProps> = ({ navigation }) => {
  const { logout } = useAuth();
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [customServerUrl, setCustomServerUrl] = useState(getApiBaseUrl());

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

  const handleUpdateServerUrl = () => {
    if (customServerUrl.trim()) {
      setApiBaseUrl(customServerUrl);
      refetch();
      Alert.alert("Server Updated", `API Base URL set to: ${getApiBaseUrl()}`);
    }
  };

  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = async () => {
    if (isLoggingOut) return;
    setIsLoggingOut(true);
    try {
      await logout();
    } catch (err) {
      console.error("Sign out error:", err);
      setIsLoggingOut(false);
    }
  };

  if (isLoading && !isRefetching) {
    return (
      <View style={styles.centerContainer}>
        <LoadingSpinner message="Loading student profile..." />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
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
        <Text style={styles.title}>Student Profile</Text>
        <Text style={styles.subtitle}>
          Verified academic and placement identity credentials.
        </Text>
      </View>

      {error && (
        <ErrorBanner
          message={(error as any).message || "Failed to load profile."}
          onRetry={refetch}
        />
      )}

      {/* Main Credentials Card */}
      <Card style={styles.infoCard}>
        <View style={styles.cardHeader}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {profile?.full_name
                ?.split(" ")
                .map((n) => n[0])
                .slice(0, 2)
                .join("")
                .toUpperCase() || "ST"}
            </Text>
          </View>
          <View style={{ flex: 1, marginLeft: 14 }}>
            <Text style={styles.fullName}>{profile?.full_name}</Text>
            <Text style={styles.emailText}>{profile?.email}</Text>
          </View>
        </View>

        <View style={styles.detailsList}>
          <View style={styles.detailRow}>
            <Building size={16} color={colors.textSecondary} />
            <Text style={styles.detailLabel}>College:</Text>
            <Text style={styles.detailValue}>{profile?.college_name}</Text>
          </View>

          <View style={styles.detailRow}>
            <GraduationCap size={16} color={colors.textSecondary} />
            <Text style={styles.detailLabel}>Branch:</Text>
            <Text style={styles.detailValue}>
              {profile?.branch} ({profile?.qualification})
            </Text>
          </View>

          <View style={styles.detailRow}>
            <Calendar size={16} color={colors.textSecondary} />
            <Text style={styles.detailLabel}>Graduation:</Text>
            <Text style={styles.detailValue}>{profile?.academic_year}</Text>
          </View>

          <View style={styles.detailRow}>
            <Award size={16} color={colors.textSecondary} />
            <Text style={styles.detailLabel}>Academic CGPA:</Text>
            <Text style={[styles.detailValue, { color: colors.accent, fontWeight: "700" }]}>
              {profile?.cgpa?.toFixed(2)}
            </Text>
          </View>

          <View style={styles.detailRow}>
            <Globe size={16} color={colors.textSecondary} />
            <Text style={styles.detailLabel}>Public ID:</Text>
            <Text style={[styles.detailValue, { fontFamily: "monospace" }]}>
              {profile?.public_profile_id}
            </Text>
          </View>
        </View>

        <View style={styles.actionRow}>
          <Button
            title="Edit Profile"
            onPress={() => setEditModalVisible(true)}
            variant="outline"
            size="small"
            icon={<Edit3 size={15} color={colors.textPrimary} />}
            style={{ flex: 1, marginRight: 8 }}
          />

          <Button
            title="Verification Link"
            onPress={() => navigation.navigate("VerificationProfile")}
            size="small"
            icon={<ExternalLink size={15} color={colors.textWhite} />}
            style={{ flex: 1 }}
          />
        </View>
      </Card>

      {/* API Server Configuration */}
      <Card style={styles.configCard}>
        <View style={styles.configHeader}>
          <Server size={18} color={colors.accent} />
          <Text style={styles.configTitle}>Backend Server Connection</Text>
        </View>
        <Text style={styles.configSubtitle}>
          Configured for testing across emulators and local LAN devices.
        </Text>

        <Input
          placeholder="http://127.0.0.1:8000"
          value={customServerUrl}
          onChangeText={setCustomServerUrl}
          autoCapitalize="none"
        />

        <Button
          title="Save Server URL & Re-sync"
          onPress={handleUpdateServerUrl}
          variant="secondary"
          size="small"
        />
      </Card>

      {/* Sign Out Button */}
      <Button
        title={isLoggingOut ? "Signing Out..." : "Sign Out"}
        onPress={handleLogout}
        variant="ghost"
        loading={isLoggingOut}
        disabled={isLoggingOut}
        icon={<LogOut size={16} color={colors.error} />}
        textStyle={{ color: colors.error }}
        style={styles.logoutBtn}
      />

      <EditProfileModal
        visible={editModalVisible}
        profile={profile}
        onClose={() => setEditModalVisible(false)}
      />
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
  infoCard: {
    padding: 18,
    marginBottom: 16,
  },
  cardHeader: {
    flexDirection: "row",
    alignItems: "center",
    borderBottomWidth: 1,
    borderBottomColor: "rgba(255,255,255,0.06)",
    paddingBottom: 16,
    marginBottom: 14,
  },
  avatar: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: "rgba(124, 58, 237, 0.2)",
    borderColor: colors.primary,
    borderWidth: 1.5,
    alignItems: "center",
    justifyContent: "center",
  },
  avatarText: {
    fontSize: 18,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  fullName: {
    fontSize: 18,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  emailText: {
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: 2,
  },
  detailsList: {
    gap: 10,
    marginBottom: 16,
  },
  detailRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  detailLabel: {
    fontSize: 13,
    color: colors.textSecondary,
    marginLeft: 8,
    width: 100,
  },
  detailValue: {
    fontSize: 13,
    color: colors.textPrimary,
    flex: 1,
  },
  actionRow: {
    flexDirection: "row",
  },
  configCard: {
    padding: 16,
    marginBottom: 16,
  },
  configHeader: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 4,
  },
  configTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: colors.textPrimary,
    marginLeft: 8,
  },
  configSubtitle: {
    fontSize: 12,
    color: colors.textSecondary,
    marginBottom: 12,
  },
  logoutBtn: {
    marginTop: 10,
  },
});
