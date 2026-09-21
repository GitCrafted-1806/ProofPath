import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { colors } from "../../theme/colors";
import { AlertCircle, RotateCcw } from "lucide-react-native";

interface ErrorBannerProps {
  message: string;
  onRetry?: () => void;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({ message, onRetry }) => {
  return (
    <View style={styles.banner}>
      <View style={styles.content}>
        <AlertCircle size={20} color={colors.error} style={styles.icon} />
        <Text style={styles.message}>{message}</Text>
      </View>
      {onRetry && (
        <TouchableOpacity style={styles.retryButton} onPress={onRetry}>
          <RotateCcw size={14} color={colors.textPrimary} style={{ marginRight: 4 }} />
          <Text style={styles.retryText}>Retry</Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  banner: {
    backgroundColor: colors.errorBg,
    borderColor: colors.error,
    borderWidth: 1,
    borderRadius: 10,
    padding: 14,
    marginVertical: 10,
  },
  content: {
    flexDirection: "row",
    alignItems: "flex-start",
  },
  icon: {
    marginRight: 10,
    marginTop: 1,
  },
  message: {
    flex: 1,
    fontSize: 13,
    color: colors.textPrimary,
    lineHeight: 18,
  },
  retryButton: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-end",
    marginTop: 8,
    backgroundColor: "rgba(255,255,255,0.08)",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  retryText: {
    fontSize: 12,
    color: colors.textPrimary,
    fontWeight: "600",
  },
});
