import React from "react";
import { View, Text, ActivityIndicator, StyleSheet } from "react-native";
import { colors } from "../../theme/colors";

interface LoadingSpinnerProps {
  message?: string;
  size?: "small" | "large";
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = "Loading...",
  size = "large",
}) => {
  return (
    <View style={styles.container}>
      <ActivityIndicator size={size} color={colors.primary} />
      {message && <Text style={styles.text}>{message}</Text>}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 24,
    alignItems: "center",
    justifyContent: "center",
  },
  text: {
    marginTop: 12,
    fontSize: 14,
    color: colors.textSecondary,
  },
});
