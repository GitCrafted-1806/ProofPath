import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  TouchableOpacity,
} from "react-native";
import { useAuth } from "../../context/AuthContext";
import { colors } from "../../theme/colors";
import { Input } from "../../components/common/Input";
import { Button } from "../../components/common/Button";
import { Card } from "../../components/common/Card";
import { ErrorBanner } from "../../components/common/ErrorBanner";
import { ShieldCheck, User } from "lucide-react-native";

interface LoginScreenProps {
  navigation: any;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({ navigation }) => {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e?: string, p?: string) => {
    const loginEmail = e || email;
    const loginPass = p || password;
    if (!loginEmail || !loginPass) {
      setError("Please provide both email and password.");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      await login(loginEmail, loginPass);
    } catch (err: any) {
      setError(err.message || "Login failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleDemoJohnDoe = () => {
    setEmail("john.doe@nit.edu");
    setPassword("Password123!");
    handleLogin("john.doe@nit.edu", "Password123!");
  };

  const handleDemoJaneSmith = () => {
    setEmail("jane.smith@nit.edu");
    setPassword("Password123!");
    handleLogin("jane.smith@nit.edu", "Password123!");
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      style={styles.container}
    >
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.header}>
          <View style={styles.logoBadge}>
            <ShieldCheck size={36} color={colors.primary} />
          </View>
          <Text style={styles.title}>ProofPath</Text>
          <Text style={styles.subtitle}>
            Evidence-based skills verification platform for campus placements.
          </Text>
        </View>

        <Card style={styles.card}>
          {/* Auth Mode Switcher */}
          <View style={styles.authTabs}>
            <View style={[styles.authTab, styles.authTabActive]}>
              <Text style={styles.authTabTextActive}>Sign In</Text>
            </View>
            <TouchableOpacity
              style={styles.authTab}
              onPress={() => navigation.navigate("Register")}
            >
              <Text style={styles.authTabText}>Create Account</Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.cardTitle}>Student Sign In</Text>

          {error && <ErrorBanner message={error} />}

          <Input
            label="College Email"
            placeholder="student@college.edu"
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            keyboardType="email-address"
          />

          <Input
            label="Password"
            placeholder="Enter your password"
            value={password}
            onChangeText={setPassword}
            isPassword
          />

          <Button
            title="Sign In"
            onPress={() => handleLogin()}
            loading={loading}
            style={styles.loginBtn}
          />

          <View style={styles.demoSection}>
            <View style={styles.divider}>
              <View style={styles.line} />
              <Text style={styles.dividerText}>DEMO ACCOUNTS</Text>
              <View style={styles.line} />
            </View>

            <Button
              title="Demo Account: John Doe"
              onPress={handleDemoJohnDoe}
              variant="secondary"
              size="small"
              icon={<User size={15} color={colors.textSecondary} />}
              style={styles.demoBtn}
            />

            <Button
              title="Demo Account: Jane Smith"
              onPress={handleDemoJaneSmith}
              variant="outline"
              size="small"
              icon={<User size={15} color={colors.textSecondary} />}
              style={styles.demoBtn}
            />
          </View>

          <View style={styles.footer}>
            <Text style={styles.footerText}>New to ProofPath? </Text>
            <TouchableOpacity onPress={() => navigation.navigate("Register")}>
              <Text style={styles.registerLink}>Create Account</Text>
            </TouchableOpacity>
          </View>
        </Card>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bgDark,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: "center",
    padding: 20,
  },
  header: {
    alignItems: "center",
    marginBottom: 28,
  },
  logoBadge: {
    width: 64,
    height: 64,
    borderRadius: 18,
    backgroundColor: "rgba(124, 58, 237, 0.12)",
    borderColor: colors.borderHighlight,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 14,
  },
  title: {
    fontSize: 28,
    fontWeight: "700",
    color: colors.textPrimary,
    letterSpacing: 0.5,
  },
  subtitle: {
    fontSize: 13,
    color: colors.textSecondary,
    textAlign: "center",
    marginTop: 6,
    maxWidth: 280,
    lineHeight: 18,
  },
  card: {
    padding: 24,
  },
  authTabs: {
    flexDirection: "row",
    backgroundColor: colors.bgDark,
    borderRadius: 10,
    padding: 4,
    marginBottom: 18,
    borderWidth: 1,
    borderColor: colors.borderDark,
  },
  authTab: {
    flex: 1,
    paddingVertical: 8,
    alignItems: "center",
    borderRadius: 8,
  },
  authTabActive: {
    backgroundColor: "rgba(124, 58, 237, 0.2)",
    borderColor: colors.primary,
    borderWidth: 1,
  },
  authTabText: {
    fontSize: 13,
    fontWeight: "600",
    color: colors.textMuted,
  },
  authTabTextActive: {
    fontSize: 13,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: colors.textPrimary,
    marginBottom: 16,
  },
  loginBtn: {
    marginTop: 8,
  },
  demoSection: {
    marginTop: 20,
  },
  divider: {
    flexDirection: "row",
    alignItems: "center",
    marginVertical: 14,
  },
  line: {
    flex: 1,
    height: 1,
    backgroundColor: colors.borderDark,
  },
  dividerText: {
    fontSize: 10,
    fontWeight: "700",
    color: colors.textMuted,
    paddingHorizontal: 8,
    letterSpacing: 0.8,
  },
  demoBtn: {
    marginBottom: 8,
  },
  footer: {
    flexDirection: "row",
    justifyContent: "center",
    marginTop: 20,
  },
  footerText: {
    fontSize: 13,
    color: colors.textSecondary,
  },
  registerLink: {
    fontSize: 13,
    fontWeight: "600",
    color: colors.primary,
  },
});
