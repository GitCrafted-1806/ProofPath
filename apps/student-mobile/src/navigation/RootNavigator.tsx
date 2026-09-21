import React from "react";
import { View, StyleSheet } from "react-native";
import { NavigationContainer } from "@react-navigation/native";
import { useAuth } from "../context/AuthContext";
import { AuthNavigator } from "./AuthNavigator";
import { MainTabNavigator } from "./MainTabNavigator";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { colors } from "../theme/colors";

export const RootNavigator: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <LoadingSpinner message="Checking ProofPath session..." />
      </View>
    );
  }

  return (
    <NavigationContainer>
      {isAuthenticated ? <MainTabNavigator /> : <AuthNavigator />}
    </NavigationContainer>
  );
};

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    backgroundColor: colors.bgDark,
    alignItems: "center",
    justifyContent: "center",
  },
});
