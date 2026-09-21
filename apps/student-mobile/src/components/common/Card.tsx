import React from "react";
import { View, StyleSheet, ViewStyle } from "react-native";
import { colors } from "../../theme/colors";

interface CardProps {
  children: React.ReactNode;
  style?: ViewStyle | ViewStyle[];
  elevated?: boolean;
}

export const Card: React.FC<CardProps> = ({ children, style, elevated = false }) => {
  return (
    <View
      style={[
        styles.card,
        elevated && styles.cardElevated,
        style,
      ]}
    >
      {children}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.cardDark,
    borderRadius: 14,
    borderColor: colors.borderDark,
    borderWidth: 1,
    padding: 16,
    marginBottom: 12,
  },
  cardElevated: {
    backgroundColor: colors.cardElevated,
    borderColor: colors.borderHighlight,
  },
});
