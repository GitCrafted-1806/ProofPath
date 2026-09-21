import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  Platform,
} from "react-native";
import * as DocumentPicker from "expo-document-picker";
import { colors } from "../../theme/colors";
import { Card } from "../../components/common/Card";
import { Button } from "../../components/common/Button";
import { ErrorBanner } from "../../components/common/ErrorBanner";
import { uploadEvidence } from "../../api/evidence";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { UploadCloud, File, X, CheckCircle2 } from "lucide-react-native";

interface EvidenceUploadModalProps {
  visible: boolean;
  onClose: () => void;
}

export const EvidenceUploadModal: React.FC<EvidenceUploadModalProps> = ({
  visible,
  onClose,
}) => {
  const queryClient = useQueryClient();
  const [selectedFile, setSelectedFile] = useState<DocumentPicker.DocumentPickerAsset | null>(null);
  const [evidenceType, setEvidenceType] = useState<"CERTIFICATE" | "PROJECT_DOCUMENT">("CERTIFICATE");
  const [error, setError] = useState<string | null>(null);

  const uploadMutation = useMutation({
    mutationFn: uploadEvidence,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["evidence"] });
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["assessments-available"] });
      setSelectedFile(null);
      setError(null);
      onClose();
    },
    onError: (err: any) => {
      setError(err.message || "Upload failed. Please check file format and size.");
    },
  });

  const pickDocument = async () => {
    try {
      setError(null);
      const result = await DocumentPicker.getDocumentAsync({
        type: ["application/pdf", "image/png", "image/jpeg"],
        copyToCacheDirectory: true,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const file = result.assets[0];
        // Check 5 MB limit
        if (file.size && file.size > 5 * 1024 * 1024) {
          setError("File exceeds maximum allowed size of 5 MB.");
          return;
        }
        setSelectedFile(file);
      }
    } catch (err: any) {
      setError("Failed to select file from device.");
    }
  };

  const handleUpload = () => {
    if (!selectedFile) {
      setError("Please select a document or certificate first.");
      return;
    }

    uploadMutation.mutate({
      uri: selectedFile.uri,
      name: selectedFile.name,
      mimeType: selectedFile.mimeType || "application/pdf",
      type: evidenceType,
      webFile: (selectedFile as any).file,
    });
  };

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <View style={styles.modalOverlay}>
        <Card style={styles.modalCard}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Upload Skill Evidence</Text>
            <TouchableOpacity onPress={onClose}>
              <X size={22} color={colors.textSecondary} />
            </TouchableOpacity>
          </View>

          {error && <ErrorBanner message={error} />}

          {/* Evidence Type Selection */}
          <Text style={styles.label}>Evidence Category</Text>
          <View style={styles.typeRow}>
            <TouchableOpacity
              style={[
                styles.typeOption,
                evidenceType === "CERTIFICATE" && styles.typeOptionActive,
              ]}
              onPress={() => setEvidenceType("CERTIFICATE")}
            >
              <Text
                style={[
                  styles.typeText,
                  evidenceType === "CERTIFICATE" && styles.typeTextActive,
                ]}
              >
                Course Certificate
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.typeOption,
                evidenceType === "PROJECT_DOCUMENT" && styles.typeOptionActive,
              ]}
              onPress={() => setEvidenceType("PROJECT_DOCUMENT")}
            >
              <Text
                style={[
                  styles.typeText,
                  evidenceType === "PROJECT_DOCUMENT" && styles.typeTextActive,
                ]}
              >
                Project Report / Doc
              </Text>
            </TouchableOpacity>
          </View>

          {/* File Picker Box */}
          <TouchableOpacity
            style={styles.pickerBox}
            activeOpacity={0.8}
            onPress={pickDocument}
          >
            {selectedFile ? (
              <View style={styles.selectedFileRow}>
                <File size={28} color={colors.accent} />
                <View style={{ flex: 1, marginLeft: 12 }}>
                  <Text style={styles.selectedFileName} numberOfLines={1}>
                    {selectedFile.name}
                  </Text>
                  <Text style={styles.selectedFileSize}>
                    {selectedFile.size
                      ? `${(selectedFile.size / 1024).toFixed(1)} KB`
                      : "Ready"}
                  </Text>
                </View>
                <CheckCircle2 size={20} color={colors.status.SKILL_VERIFIED.text} />
              </View>
            ) : (
              <View style={styles.pickerEmpty}>
                <UploadCloud size={36} color={colors.primary} />
                <Text style={styles.pickerTitle}>Tap to select document</Text>
                <Text style={styles.pickerSubtitle}>
                  Supports PDF, PNG, JPG (Max 5 MB)
                </Text>
              </View>
            )}
          </TouchableOpacity>

          <Button
            title="Upload & Parse Document"
            onPress={handleUpload}
            loading={uploadMutation.isPending}
            disabled={!selectedFile}
            style={styles.uploadBtn}
          />
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
    padding: 24,
    borderWidth: 1,
    borderColor: colors.borderHighlight,
    marginBottom: 0,
  },
  modalHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  label: {
    fontSize: 13,
    fontWeight: "600",
    color: colors.textSecondary,
    marginBottom: 8,
  },
  typeRow: {
    flexDirection: "row",
    gap: 10,
    marginBottom: 16,
  },
  typeOption: {
    flex: 1,
    backgroundColor: colors.cardDark,
    borderColor: colors.borderDark,
    borderWidth: 1,
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: "center",
  },
  typeOptionActive: {
    borderColor: colors.primary,
    backgroundColor: "rgba(124, 58, 237, 0.15)",
  },
  typeText: {
    fontSize: 12,
    color: colors.textSecondary,
    fontWeight: "500",
  },
  typeTextActive: {
    color: colors.textPrimary,
    fontWeight: "700",
  },
  pickerBox: {
    backgroundColor: colors.cardDark,
    borderColor: colors.borderDark,
    borderWidth: 1.5,
    borderStyle: "dashed",
    borderRadius: 12,
    padding: 20,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 20,
  },
  pickerEmpty: {
    alignItems: "center",
  },
  pickerTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: colors.textPrimary,
    marginTop: 8,
  },
  pickerSubtitle: {
    fontSize: 12,
    color: colors.textMuted,
    marginTop: 4,
  },
  selectedFileRow: {
    flexDirection: "row",
    alignItems: "center",
    width: "100%",
  },
  selectedFileName: {
    fontSize: 14,
    fontWeight: "600",
    color: colors.textPrimary,
  },
  selectedFileSize: {
    fontSize: 12,
    color: colors.textMuted,
    marginTop: 2,
  },
  uploadBtn: {
    marginTop: 4,
  },
});
