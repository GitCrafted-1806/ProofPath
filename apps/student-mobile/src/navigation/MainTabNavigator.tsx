import React from "react";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { DashboardScreen } from "../screens/dashboard/DashboardScreen";
import { SkillsScreen } from "../screens/skills/SkillsScreen";
import { SkillDetailScreen } from "../screens/skills/SkillDetailScreen";
import { EvidenceScreen } from "../screens/evidence/EvidenceScreen";
import { GitHubScreen } from "../screens/github/GitHubScreen";
import { AssessmentsListScreen } from "../screens/assessments/AssessmentsListScreen";
import { AssessmentTakeScreen } from "../screens/assessments/AssessmentTakeScreen";
import { AssessmentResultScreen } from "../screens/assessments/AssessmentResultScreen";
import { ProfileScreen } from "../screens/profile/ProfileScreen";
import { VerificationProfileScreen } from "../screens/verification/VerificationProfileScreen";
import { colors } from "../theme/colors";
import {
  LayoutDashboard,
  Award,
  FileText,
  CheckSquare,
  User,
} from "lucide-react-native";

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

function SkillsStackNavigator() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: colors.bgDark },
      }}
    >
      <Stack.Screen name="SkillsMain" component={SkillsScreen} />
      <Stack.Screen name="SkillDetail" component={SkillDetailScreen} />
      <Stack.Screen name="VerificationProfile" component={VerificationProfileScreen} />
    </Stack.Navigator>
  );
}

function AssessmentsStackNavigator() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: colors.bgDark },
      }}
    >
      <Stack.Screen name="AssessmentsMain" component={AssessmentsListScreen} />
      <Stack.Screen name="AssessmentTake" component={AssessmentTakeScreen} />
      <Stack.Screen name="AssessmentResult" component={AssessmentResultScreen} />
    </Stack.Navigator>
  );
}

function ProfileStackNavigator() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: colors.bgDark },
      }}
    >
      <Stack.Screen name="ProfileMain" component={ProfileScreen} />
      <Stack.Screen name="GitHub" component={GitHubScreen} />
      <Stack.Screen name="VerificationProfile" component={VerificationProfileScreen} />
    </Stack.Navigator>
  );
}

export const MainTabNavigator: React.FC = () => {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: colors.cardDark,
          borderTopColor: colors.borderDark,
          borderTopWidth: 1,
          height: 60,
          paddingBottom: 8,
          paddingTop: 6,
        },
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: "600",
        },
      }}
    >
      <Tab.Screen
        name="Dashboard"
        component={DashboardScreen}
        options={{
          tabBarLabel: "Dashboard",
          tabBarIcon: ({ color, size }) => (
            <LayoutDashboard size={size || 20} color={color} />
          ),
        }}
      />

      <Tab.Screen
        name="Skills"
        component={SkillsStackNavigator}
        options={{
          tabBarLabel: "Skills",
          tabBarIcon: ({ color, size }) => (
            <Award size={size || 20} color={color} />
          ),
        }}
      />

      <Tab.Screen
        name="Evidence"
        component={EvidenceScreen}
        options={{
          tabBarLabel: "Evidence",
          tabBarIcon: ({ color, size }) => (
            <FileText size={size || 20} color={color} />
          ),
        }}
      />

      <Tab.Screen
        name="Assessments"
        component={AssessmentsStackNavigator}
        options={{
          tabBarLabel: "Assessments",
          tabBarIcon: ({ color, size }) => (
            <CheckSquare size={size || 20} color={color} />
          ),
        }}
      />

      <Tab.Screen
        name="Profile"
        component={ProfileStackNavigator}
        options={{
          tabBarLabel: "Profile",
          tabBarIcon: ({ color, size }) => (
            <User size={size || 20} color={color} />
          ),
        }}
      />
    </Tab.Navigator>
  );
};
