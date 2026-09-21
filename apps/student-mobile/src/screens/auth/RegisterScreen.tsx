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
import {
  UserPlus,
  GraduationCap,
  Award,
  CheckCircle2,
  Circle,
  ArrowRight,
  ArrowLeft,
  Shield,
} from "lucide-react-native";

const MVP_SKILLS = ["Python", "Pandas", "Matplotlib", "Git/GitHub"];

interface RegisterScreenProps {
  navigation: any;
}

export const RegisterScreen: React.FC<RegisterScreenProps> = ({ navigation }) => {
  const { register } = useAuth();
  const [step, setStep] = useState<1 | 2 | 3>(1);

  // Step 1: Basic student details
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // Step 2: Academic details
  const [collegeName, setCollegeName] = useState("");
  const [branch, setBranch] = useState("");
  const [academicYear, setAcademicYear] = useState("");
  const [cgpa, setCgpa] = useState("");

  // Step 3: Claimed MVP skills
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStep1Next = () => {
    const nameTrim = fullName.trim();
    if (!nameTrim) {
      setError("Please enter your full name.");
      return;
    }
    if (nameTrim.length < 2 || nameTrim.length > 80) {
      setError("Name must contain between 2 and 80 characters.");
      return;
    }
    if (/\d/.test(nameTrim)) {
      setError("Name cannot contain numbers.");
      return;
    }
    const letters = nameTrim.match(/[a-zA-Z]/g) || [];
    if (!/^[a-zA-Z\s'\-\.]+$/.test(nameTrim) || letters.length < 2) {
      setError("Name can only contain letters, spaces, hyphens, apostrophes, and periods.");
      return;
    }
    if (!email.trim() || !email.includes("@")) {
      setError("Please enter a valid college email address.");
      return;
    }
    if (!password || password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setError(null);
    setStep(2);
  };

  const handleStep2Next = () => {
    const collegeTrim = collegeName.trim();
    if (!collegeTrim) {
      setError("Please enter your college or institution name.");
      return;
    }
    if (collegeTrim.length < 2 || collegeTrim.length > 120) {
      setError("College name must be between 2 and 120 characters.");
      return;
    }
    if (!/^[a-zA-Z0-9\s&.\-'\/\(\)]+$/.test(collegeTrim)) {
      setError("College/institution name contains invalid characters.");
      return;
    }

    const branchTrim = branch.trim();
    if (!branchTrim) {
      setError("Please enter your branch or major (e.g. CSE).");
      return;
    }
    if (branchTrim.length < 2 || branchTrim.length > 80) {
      setError("Branch must be between 2 and 80 characters.");
      return;
    }
    if (!/^[a-zA-Z0-9\s&/\-\.]+$/.test(branchTrim)) {
      setError("Branch/major contains invalid characters.");
      return;
    }

    const yearNum = parseInt(academicYear.trim(), 10);
    if (!academicYear.trim() || isNaN(yearNum) || yearNum < 2000 || yearNum > 2040) {
      setError("Graduation year must be a 4-digit year between 2000 and 2040.");
      return;
    }

    const cgpaNum = parseFloat(cgpa.trim());
    if (!cgpa.trim() || isNaN(cgpaNum) || cgpaNum < 0.0 || cgpaNum > 10.0) {
      setError("Enter a valid CGPA between 0 and 10.");
      return;
    }
    if (cgpa.trim().includes(".") && cgpa.trim().split(".")[1].length > 2) {
      setError("CGPA cannot have more than 2 decimal places.");
      return;
    }

    setError(null);
    setStep(3);
  };

  const toggleSkill = (skill: string) => {
    if (selectedSkills.includes(skill)) {
      setSelectedSkills(selectedSkills.filter((s) => s !== skill));
    } else {
      setSelectedSkills([...selectedSkills, skill]);
    }
  };

  const handleRegister = async () => {
    if (selectedSkills.length === 0) {
      setError("Please select at least one claimed MVP skill.");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      await register({
        full_name: fullName.trim(),
        email: email.trim(),
        password,
        college_name: collegeName.trim(),
        branch: branch.trim(),
        academic_year: parseInt(academicYear.trim(), 10),
        cgpa: parseFloat(cgpa.trim()),
        qualification: "B.Tech",
        skills: selectedSkills,
      });
    } catch (err: any) {
      setError(err.message || "Registration failed. Please verify your details.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      style={styles.container}
    >
      <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <View style={styles.logoBadge}>
            <UserPlus size={30} color={colors.primary} />
          </View>
          <Text style={styles.title}>Create Account</Text>
          <Text style={styles.subtitle}>
            Evidence-based student verification for campus placements.
          </Text>
        </View>

        {/* Step Progress Indicator */}
        <View style={styles.stepBarContainer}>
          <TouchableOpacity
            style={[styles.stepTab, step === 1 && styles.stepTabActive]}
            onPress={() => setStep(1)}
          >
            <Text style={[styles.stepTabText, step === 1 && styles.stepTabTextActive]}>
              1. Basics
            </Text>
          </TouchableOpacity>
          <View style={styles.stepDivider} />
          <TouchableOpacity
            style={[styles.stepTab, step === 2 && styles.stepTabActive]}
            onPress={() => {
              if (fullName && email && password.length >= 6) setStep(2);
            }}
          >
            <Text style={[styles.stepTabText, step === 2 && styles.stepTabTextActive]}>
              2. Academic
            </Text>
          </TouchableOpacity>
          <View style={styles.stepDivider} />
          <TouchableOpacity
            style={[styles.stepTab, step === 3 && styles.stepTabActive]}
            onPress={() => {
              if (fullName && email && collegeName && branch && cgpa) setStep(3);
            }}
          >
            <Text style={[styles.stepTabText, step === 3 && styles.stepTabTextActive]}>
              3. Skills
            </Text>
          </TouchableOpacity>
        </View>

        <Card style={styles.card}>
          {error && <ErrorBanner message={error} />}

          {/* STEP 1: Basic Student Details */}
          {step === 1 && (
            <View>
              <Text style={styles.stepTitle}>Basic Information</Text>
              <Text style={styles.stepDesc}>
                Provide your identity details for college records.
              </Text>

              <Input
                label="Full Name *"
                placeholder="e.g. Alex Chen"
                value={fullName}
                onChangeText={setFullName}
                autoCapitalize="words"
              />

              <Input
                label="College Email *"
                placeholder="e.g. alex.chen@nit.edu"
                value={email}
                onChangeText={setEmail}
                autoCapitalize="none"
                keyboardType="email-address"
              />

              <Input
                label="Password *"
                placeholder="At least 6 characters"
                value={password}
                onChangeText={setPassword}
                isPassword
              />

              <Button
                title="Continue to Academic Details"
                onPress={handleStep1Next}
                icon={<ArrowRight size={16} color={colors.textWhite} />}
                style={styles.actionBtn}
              />
            </View>
          )}

          {/* STEP 2: Academic Details */}
          {step === 2 && (
            <View>
              <Text style={styles.stepTitle}>Academic Profile</Text>
              <Text style={styles.stepDesc}>
                Specify your institution and official academic standing.
              </Text>

              <Input
                label="College / Institution *"
                placeholder="e.g. National Institute of Technology"
                value={collegeName}
                onChangeText={setCollegeName}
              />

              <Input
                label="Branch / Major *"
                placeholder="e.g. Computer Science & Engineering"
                value={branch}
                onChangeText={setBranch}
              />

              <View style={styles.row}>
                <View style={{ flex: 1, marginRight: 8 }}>
                  <Input
                    label="Graduation Year *"
                    placeholder="e.g. 2026"
                    value={academicYear}
                    onChangeText={setAcademicYear}
                    keyboardType="numeric"
                  />
                </View>
                <View style={{ flex: 1, marginLeft: 8 }}>
                  <Input
                    label="CGPA (0.0 - 10.0) *"
                    placeholder="e.g. 8.4"
                    value={cgpa}
                    onChangeText={setCgpa}
                    keyboardType="numeric"
                  />
                </View>
              </View>

              <View style={styles.buttonRow}>
                <Button
                  title="Back"
                  onPress={() => {
                    setError(null);
                    setStep(1);
                  }}
                  variant="secondary"
                  icon={<ArrowLeft size={16} color={colors.textPrimary} />}
                  style={{ flex: 1, marginRight: 8 }}
                />
                <Button
                  title="Next: Skills"
                  onPress={handleStep2Next}
                  icon={<ArrowRight size={16} color={colors.textWhite} />}
                  style={{ flex: 2, marginLeft: 8 }}
                />
              </View>
            </View>
          )}

          {/* STEP 3: Skill Selection */}
          {step === 3 && (
            <View>
              <Text style={styles.stepTitle}>Claimed MVP Skills</Text>
              <Text style={styles.stepDesc}>
                Select the ProofPath MVP skills you claim proficiency in.
              </Text>

              <View style={styles.verificationNoteCard}>
                <Shield size={16} color={colors.accent} style={{ marginTop: 2, marginRight: 8 }} />
                <Text style={styles.verificationNoteText}>
                  Claimed skills start strictly as <Text style={{ color: colors.textPrimary, fontWeight: "600" }}>Unverified</Text>. Verification status advances only through genuine evidence and assessments.
                </Text>
              </View>

              <View style={styles.skillsListContainer}>
                {MVP_SKILLS.map((skillName) => {
                  const isSelected = selectedSkills.includes(skillName);
                  return (
                    <TouchableOpacity
                      key={skillName}
                      style={[
                        styles.skillSelectionCard,
                        isSelected && styles.skillSelectionCardActive,
                      ]}
                      onPress={() => toggleSkill(skillName)}
                      activeOpacity={0.7}
                    >
                      <View style={styles.skillSelectionLeft}>
                        {isSelected ? (
                          <CheckCircle2 size={20} color={colors.primary} />
                        ) : (
                          <Circle size={20} color={colors.textMuted} />
                        )}
                        <Text
                          style={[
                            styles.skillSelectionName,
                            isSelected && styles.skillSelectionNameActive,
                          ]}
                        >
                          {skillName}
                        </Text>
                      </View>
                      <View
                        style={[
                          styles.claimBadge,
                          isSelected && styles.claimBadgeActive,
                        ]}
                      >
                        <Text
                          style={[
                            styles.claimBadgeText,
                            isSelected && styles.claimBadgeTextActive,
                          ]}
                        >
                          {isSelected ? "CLAIMED" : "TAP TO CLAIM"}
                        </Text>
                      </View>
                    </TouchableOpacity>
                  );
                })}
              </View>

              <Text style={styles.skillsCounter}>
                Selected: {selectedSkills.length} of {MVP_SKILLS.length} skills (minimum 1 required)
              </Text>

              <View style={styles.buttonRow}>
                <Button
                  title="Back"
                  onPress={() => {
                    setError(null);
                    setStep(2);
                  }}
                  variant="secondary"
                  icon={<ArrowLeft size={16} color={colors.textPrimary} />}
                  style={{ flex: 1, marginRight: 8 }}
                />
                <Button
                  title="Complete Registration"
                  onPress={handleRegister}
                  loading={loading}
                  icon={<CheckCircle2 size={16} color={colors.textWhite} />}
                  style={{ flex: 2, marginLeft: 8 }}
                />
              </View>
            </View>
          )}

          <View style={styles.footer}>
            <Text style={styles.footerText}>Already have an account? </Text>
            <TouchableOpacity onPress={() => navigation.navigate("Login")}>
              <Text style={styles.loginLink}>Sign In</Text>
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
    padding: 20,
    justifyContent: "center",
  },
  header: {
    alignItems: "center",
    marginBottom: 16,
  },
  logoBadge: {
    width: 52,
    height: 52,
    borderRadius: 14,
    backgroundColor: "rgba(124, 58, 237, 0.12)",
    borderColor: colors.borderHighlight,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 8,
  },
  title: {
    fontSize: 22,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  subtitle: {
    fontSize: 13,
    color: colors.textSecondary,
    textAlign: "center",
    marginTop: 4,
    maxWidth: 290,
  },
  stepBarContainer: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: colors.cardDark,
    borderRadius: 10,
    padding: 4,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: colors.borderDark,
  },
  stepTab: {
    flex: 1,
    paddingVertical: 8,
    alignItems: "center",
    borderRadius: 6,
  },
  stepTabActive: {
    backgroundColor: "rgba(124, 58, 237, 0.2)",
    borderWidth: 1,
    borderColor: colors.primary,
  },
  stepTabText: {
    fontSize: 12,
    fontWeight: "600",
    color: colors.textMuted,
  },
  stepTabTextActive: {
    color: colors.textPrimary,
  },
  stepDivider: {
    width: 1,
    height: 16,
    backgroundColor: colors.borderDark,
  },
  card: {
    padding: 20,
  },
  stepTitle: {
    fontSize: 17,
    fontWeight: "600",
    color: colors.textPrimary,
    marginBottom: 4,
  },
  stepDesc: {
    fontSize: 13,
    color: colors.textSecondary,
    marginBottom: 16,
  },
  row: {
    flexDirection: "row",
  },
  buttonRow: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 14,
  },
  actionBtn: {
    marginTop: 10,
  },
  verificationNoteCard: {
    flexDirection: "row",
    backgroundColor: "rgba(6, 182, 212, 0.08)",
    borderWidth: 1,
    borderColor: "rgba(6, 182, 212, 0.2)",
    borderRadius: 8,
    padding: 10,
    marginBottom: 14,
  },
  verificationNoteText: {
    flex: 1,
    fontSize: 12,
    color: colors.textSecondary,
    lineHeight: 16,
  },
  skillsListContainer: {
    gap: 8,
    marginBottom: 10,
  },
  skillSelectionCard: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: colors.cardElevated,
    borderWidth: 1,
    borderColor: colors.borderDark,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  skillSelectionCardActive: {
    borderColor: colors.primary,
    backgroundColor: "rgba(124, 58, 237, 0.1)",
  },
  skillSelectionLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  skillSelectionName: {
    fontSize: 14,
    fontWeight: "600",
    color: colors.textSecondary,
  },
  skillSelectionNameActive: {
    color: colors.textPrimary,
  },
  claimBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    backgroundColor: colors.bgDark,
    borderWidth: 1,
    borderColor: colors.borderDark,
  },
  claimBadgeActive: {
    backgroundColor: "rgba(124, 58, 237, 0.25)",
    borderColor: colors.primary,
  },
  claimBadgeText: {
    fontSize: 10,
    fontWeight: "700",
    color: colors.textMuted,
  },
  claimBadgeTextActive: {
    color: colors.textPrimary,
  },
  skillsCounter: {
    fontSize: 12,
    color: colors.textSecondary,
    textAlign: "right",
    marginBottom: 6,
  },
  footer: {
    flexDirection: "row",
    justifyContent: "center",
    marginTop: 18,
  },
  footerText: {
    fontSize: 13,
    color: colors.textSecondary,
  },
  loginLink: {
    fontSize: 13,
    fontWeight: "600",
    color: colors.primary,
  },
});
