import React from "react";
import {
  TouchableOpacity,
  Text,
  ActivityIndicator,
  StyleSheet,
  ViewStyle,
  TextStyle,
} from "react-native";
import { colors } from "../../theme/colors";

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: "primary" | "secondary" | "outline" | "danger" | "ghost";
  size?: "small" | "medium" | "large";
  loading?: boolean;
  disabled?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  variant = "primary",
  size = "medium",
  loading = false,
  disabled = false,
  style,
  textStyle,
  icon,
}) => {
  const getBackgroundColor = () => {
    if (disabled) return "#1E293B";
    switch (variant) {
      case "primary":
        return colors.primary;
      case "secondary":
        return colors.cardElevated;
      case "danger":
        return colors.error;
      case "outline":
      case "ghost":
        return "transparent";
      default:
        return colors.primary;
    }
  };

  const getBorderColor = () => {
    if (variant === "outline") return disabled ? "#334155" : colors.primary;
    return "transparent";
  };

  const getTextColor = () => {
    if (disabled) return colors.textMuted;
    if (variant === "outline" || variant === "ghost") return colors.textPrimary;
    return colors.textWhite;
  };

  const getPadding = () => {
    switch (size) {
      case "small":
        return { paddingVertical: 8, paddingHorizontal: 14 };
      case "large":
        return { paddingVertical: 16, paddingHorizontal: 24 };
      default:
        return { paddingVertical: 12, paddingHorizontal: 18 };
    }
  };

  return (
    <TouchableOpacity
      activeOpacity={0.8}
      onPress={onPress}
      disabled={disabled || loading}
      style={[
        styles.button,
        getPadding(),
        {
          backgroundColor: getBackgroundColor(),
          borderColor: getBorderColor(),
          borderWidth: variant === "outline" ? 1 : 0,
        },
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={getTextColor()} size="small" />
      ) : (
        <>
          {icon && <>{icon}</>}
          <Text style={[styles.text, { color: getTextColor() }, textStyle]}>
            {title}
          </Text>
        </>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    borderRadius: 10,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  text: {
    fontSize: 15,
    fontWeight: "600",
    letterSpacing: 0.2,
  },
});
