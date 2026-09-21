import React from "react";
import { View, Text, StyleSheet, ViewStyle, TextStyle } from "react-native";
import { colors } from "../../theme/colors";

interface BadgeProps {
  label: string;
  textColor?: string;
  bgColor?: string;
  borderColor?: string;
  icon?: React.ReactNode;
  style?: ViewStyle;
  textStyle?: TextStyle;
}

export const Badge: React.FC<BadgeProps> = ({
  label,
  textColor = colors.textPrimary,
  bgColor = "rgba(124, 58, 237, 0.12)",
  borderColor,
  icon,
  style,
  textStyle,
}) => {
  return (
    <View
      style={[
        styles.badge,
        {
          backgroundColor: bgColor,
          borderColor: borderColor || bgColor,
          borderWidth: borderColor ? 1 : 0,
        },
        style,
      ]}
    >
      {icon && <View style={styles.icon}>{icon}</View>}
      <Text style={[styles.text, { color: textColor }, textStyle]}>{label}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    alignSelf: "flex-start",
  },
  icon: {
    marginRight: 4,
  },
  text: {
    fontSize: 11,
    fontWeight: "600",
    letterSpacing: 0.1,
  },
});
