import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { SkillVerificationStatus } from "../../types";
import { colors } from "../../theme/colors";
import { CheckCircle, Award, FileCheck, Circle } from "lucide-react-native";

interface SkillStatusBadgeProps {
  status: SkillVerificationStatus;
  size?: "small" | "medium";
}

export const SkillStatusBadge: React.FC<SkillStatusBadgeProps> = ({
  status,
  size = "medium",
}) => {
  const cfg = colors.status[status] || colors.status.UNVERIFIED;
  const isSmall = size === "small";

  const renderIcon = () => {
    const iconSize = isSmall ? 12 : 14;
    switch (status) {
      case "SKILL_VERIFIED":
        return <CheckCircle size={iconSize} color={cfg.text} />;
      case "SKILL_ASSESSED":
        return <Award size={iconSize} color={cfg.text} />;
      case "EVIDENCE_SUPPORTED":
        return <FileCheck size={iconSize} color={cfg.text} />;
      default:
        return <Circle size={iconSize} color={cfg.text} />;
    }
  };

  return (
    <View
      style={[
        styles.badge,
        {
          backgroundColor: cfg.bg,
          borderColor: cfg.border,
          paddingVertical: isSmall ? 3 : 5,
          paddingHorizontal: isSmall ? 7 : 10,
        },
      ]}
    >
      <View style={styles.icon}>{renderIcon()}</View>
      <Text
        style={[
          styles.text,
          {
            color: cfg.text,
            fontSize: isSmall ? 11 : 12,
          },
        ]}
      >
        {cfg.label}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: {
    flexDirection: "row",
    alignItems: "center",
    borderRadius: 8,
    borderWidth: 1,
    alignSelf: "flex-start",
  },
  icon: {
    marginRight: 5,
  },
  text: {
    fontWeight: "600",
    letterSpacing: 0.1,
  },
});
