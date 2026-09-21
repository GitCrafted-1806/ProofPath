import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  Modal,
  ScrollView,
  TouchableOpacity,
  Switch,
} from "react-native";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateStudentProfile } from "../../api/students";
import { StudentProfileResponse } from "../../types";
import { colors } from "../../theme/colors";
import { Card } from "../../components/common/Card";
import { Button } from "../../components/common/Button";
import { Input } from "../../components/common/Input";
import { ErrorBanner } from "../../components/common/ErrorBanner";
import { X, Check } from "lucide-react-native";

interface EditProfileModalProps {
  visible: boolean;
  profile?: StudentProfileResponse;
  onClose: () => void;
}

export const EditProfileModal: React.FC<EditProfileModalProps> = ({
  visible,
  profile,
  onClose,
}) => {
  const queryClient = useQueryClient();

  const [fullName, setFullName] = useState(profile?.full_name || "");
  const [collegeName, setCollegeName] = useState(profile?.college_name || "");
  const [branch, setBranch] = useState(profile?.branch || "");
  const [academicYear, setAcademicYear] = useState(String(profile?.academic_year || "2026"));
  const [cgpa, setCgpa] = useState(String(profile?.cgpa || "8.0"));
  const [qualification, setQualification] = useState(profile?.qualification || "B.Tech");
  const [isPublic, setIsPublic] = useState(profile?.is_public ?? true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (profile) {
      setFullName(profile.full_name || "");
      setCollegeName(profile.college_name || "");
      setBranch(profile.branch || "");
      setAcademicYear(String(profile.academic_year || "2026"));
      setCgpa(String(profile.cgpa || "8.0"));
      setQualification(profile.qualification || "B.Tech");
      setIsPublic(profile.is_public ?? true);
    }
  }, [profile, visible]);

  const updateMutation = useMutation({
    mutationFn: updateStudentProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      onClose();
    },
    onError: (err: any) => {
      setError(err.message || "Failed to update profile.");
    },
  });

  const handleSave = () => {
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
      setError("Please enter a valid full name using letters and standard name punctuation.");
      return;
    }

    const collegeTrim = collegeName.trim();
    if (!collegeTrim) {
      setError("Please enter your college or institution name.");
      return;
    }
    if (collegeTrim.length < 2 || collegeTrim.length > 120) {
      setError("College/institution name must be between 2 and 120 characters.");
      return;
    }

    const branchTrim = branch.trim();
    if (!branchTrim) {
      setError("Please enter your branch or department.");
      return;
    }
    if (branchTrim.length < 2 || branchTrim.length > 80) {
      setError("Branch/major must be between 2 and 80 characters.");
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
    updateMutation.mutate({
      full_name: nameTrim,
      college_name: collegeTrim,
      branch: branchTrim,
      qualification: qualification.trim() || "B.Tech",
      academic_year: yearNum,
      cgpa: Math.round(cgpaNum * 100) / 100,
      is_public: isPublic,
    });
  };

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <View style={styles.modalOverlay}>
        <Card style={styles.modalCard}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Edit Academic Profile</Text>
            <TouchableOpacity onPress={onClose}>
              <X size={22} color={colors.textSecondary} />
            </TouchableOpacity>
          </View>

          {error && <ErrorBanner message={error} />}

          <ScrollView style={styles.formScroll} showsVerticalScrollIndicator={false}>
            <Input
              label="Full Name"
              value={fullName}
              onChangeText={setFullName}
            />

            <Input
              label="College / Institute"
              value={collegeName}
              onChangeText={setCollegeName}
            />

            <View style={styles.row}>
              <View style={{ flex: 1, marginRight: 8 }}>
                <Input
                  label="Branch / Major"
                  value={branch}
                  onChangeText={setBranch}
                />
              </View>
              <View style={{ width: 100 }}>
                <Input
                  label="Degree"
                  value={qualification}
                  onChangeText={setQualification}
                />
              </View>
            </View>

            <View style={styles.row}>
              <View style={{ flex: 1, marginRight: 8 }}>
                <Input
                  label="Graduation Year"
                  value={academicYear}
                  onChangeText={setAcademicYear}
                  keyboardType="numeric"
                />
              </View>
              <View style={{ width: 100 }}>
                <Input
                  label="CGPA"
                  value={cgpa}
                  onChangeText={setCgpa}
                  keyboardType="numeric"
                />
              </View>
            </View>

            <View style={styles.switchRow}>
              <View style={{ flex: 1, marginRight: 10 }}>
                <Text style={styles.switchLabel}>Public Profile Visibility</Text>
                <Text style={styles.switchSublabel}>
                  Allow recruiters and coordinators to view verified portfolio via link
                </Text>
              </View>
              <Switch
                value={isPublic}
                onValueChange={setIsPublic}
                trackColor={{ false: "#334155", true: colors.primary }}
                thumbColor={colors.textWhite}
              />
            </View>

            <Button
              title="Save & Persist Changes"
              onPress={handleSave}
              loading={updateMutation.isPending}
              style={styles.saveBtn}
            />
          </ScrollView>
        </Card>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.75)",
    justifyContent: "flex-end",
  },
  modalCard: {
    backgroundColor: colors.cardElevated,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 22,
    maxHeight: "85%",
    borderColor: colors.borderHighlight,
    marginBottom: 0,
  },
  modalHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 14,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  formScroll: {
    maxHeight: 450,
  },
  row: {
    flexDirection: "row",
  },
  switchRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: colors.cardDark,
    padding: 12,
    borderRadius: 10,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: colors.borderDark,
  },
  switchLabel: {
    fontSize: 13,
    fontWeight: "600",
    color: colors.textPrimary,
  },
  switchSublabel: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 2,
    lineHeight: 14,
  },
  saveBtn: {
    marginTop: 4,
    marginBottom: 10,
  },
});
