"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Download,
  FileCheck,
  FileText,
  HelpCircle,
  Loader2,
  Paperclip,
  Plus,
  RefreshCw,
  Send,
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { api, ApiError } from "@/lib/api";
import { ProjectFileItem, ProjectStatus, RevisionItem, RevisionStatus } from "@/types";
import { alertVariants, buttonPressProps, fadeUpVariants } from "@/lib/motion";

interface ProjectRevisionsProps {
  projectId: string;
  projectStatus: ProjectStatus;
  revisionsUsed: number;
  onRevisionSubmitted?: () => void;
}

const STATUS_CONFIG: Record<
  RevisionStatus,
  { label: string; bg: string; text: string; border: string; icon: typeof Clock }
> = {
  PENDING: {
    label: "Under Studio Review",
    bg: "bg-amber-50",
    text: "text-amber-800",
    border: "border-amber-200",
    icon: Clock,
  },
  IN_PROGRESS: {
    label: "In Progress",
    bg: "bg-blue-50",
    text: "text-blue-800",
    border: "border-blue-200",
    icon: RefreshCw,
  },
  COMPLETED: {
    label: "Resolved & Applied",
    bg: "bg-emerald-50",
    text: "text-emerald-800",
    border: "border-emerald-200",
    icon: CheckCircle2,
  },
  REJECTED: {
    label: "Declined",
    bg: "bg-slate-100",
    text: "text-slate-700",
    border: "border-slate-300",
    icon: AlertCircle,
  },
};

export default function ProjectRevisions({
  projectId,
  projectStatus,
  revisionsUsed,
  onRevisionSubmitted,
}: ProjectRevisionsProps) {
  const [revisions, setRevisions] = useState<RevisionItem[]>([]);
  const [availableFiles, setAvailableFiles] = useState<ProjectFileItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [description, setDescription] = useState("");
  const [selectedAttachmentIds, setSelectedAttachmentIds] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const isEligibleForRevisions =
    projectStatus !== "NEW" && projectStatus !== "REQUIREMENTS_PENDING";

  const loadRevisions = useCallback(async () => {
    try {
      const res = await api.get<RevisionItem[]>(`/projects/${projectId}/revisions`);
      if (res.success && res.data) {
        setRevisions(res.data);
      }
    } catch {
      // Non-fatal if revisions cannot be loaded initially
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  const loadProjectFiles = useCallback(async () => {
    try {
      const res = await api.get<ProjectFileItem[]>(`/projects/${projectId}/files`);
      if (res.success && res.data) {
        setAvailableFiles(res.data);
      }
    } catch {
      // Ignore
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId) {
      loadRevisions();
      loadProjectFiles();
    }
  }, [projectId, loadRevisions, loadProjectFiles]);

  const toggleAttachment = (fileId: string) => {
    setSelectedAttachmentIds((prev) =>
      prev.includes(fileId) ? prev.filter((id) => id !== fileId) : [...prev, fileId]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    const trimmed = description.trim();
    if (trimmed.length < 10) {
      setError("Please describe the requested changes with at least 10 characters.");
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await api.post<RevisionItem>(`/projects/${projectId}/revisions`, {
        description: trimmed,
        attachment_file_ids: selectedAttachmentIds,
      });

      if (res.success && res.data) {
        setSuccess(res.message || "Revision request submitted successfully.");
        setDescription("");
        setSelectedAttachmentIds([]);
        setShowForm(false);
        await loadRevisions();
        if (onRevisionSubmitted) {
          onRevisionSubmitted();
        }
      } else {
        setError(res.message || "Failed to submit revision request.");
      }
    } catch (err: any) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred while submitting your revision.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">
              Revisions & Feedback
            </h2>
            <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-700">
              {revisions.length} {revisions.length === 1 ? "round" : "rounds"} logged
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Submit iterative feedback, request layout changes, and track studio resolutions.
          </p>
        </div>

        {isEligibleForRevisions && !showForm && (
          <motion.div {...buttonPressProps}>
            <button
              type="button"
              onClick={() => {
                setShowForm(true);
                setError(null);
                setSuccess(null);
              }}
              className="inline-flex items-center gap-1.5 rounded-lg bg-slate-900 px-3.5 py-2 text-xs font-semibold text-white hover:bg-slate-800 transition-colors shadow-sm"
            >
              <Plus className="h-3.5 w-3.5" />
              Request Revision
            </button>
          </motion.div>
        )}
      </div>

      {/* Ineligible Notice */}
      {!isEligibleForRevisions && (
        <div className="mt-5 rounded-lg border border-amber-200 bg-amber-50/70 p-4 text-xs text-amber-800 flex items-start gap-2.5">
          <HelpCircle className="h-4 w-4 shrink-0 text-amber-600 mt-0.5" />
          <div>
            <p className="font-semibold text-amber-900">Revisions unlock during review phases</p>
            <p className="mt-0.5 text-amber-700 leading-relaxed">
              Once initial project requirements are submitted and our studio team completes the first build milestone, you will be able to submit revision requests directly from this panel.
            </p>
          </div>
        </div>
      )}

      {/* Feedback Messages */}
      <AnimatePresence>
        {error && (
          <motion.div
            variants={alertVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="mt-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700"
          >
            <AlertCircle className="h-4 w-4 shrink-0 text-red-500 mt-0.5" />
            <span className="leading-relaxed">{error}</span>
          </motion.div>
        )}
        {success && (
          <motion.div
            variants={alertVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="mt-4 flex items-start gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-800"
          >
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600 mt-0.5" />
            <span className="leading-relaxed">{success}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Revision Request Form */}
      <AnimatePresence>
        {showForm && (
          <motion.form
            variants={fadeUpVariants}
            initial="hidden"
            animate="visible"
            exit="hidden"
            onSubmit={handleSubmit}
            className="mt-6 rounded-lg border border-slate-200 bg-slate-50/60 p-5"
          >
            <div className="flex items-center justify-between pb-3 border-b border-slate-200/80 mb-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                New Revision Request (#{revisions.length + 1})
              </h3>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="text-xs text-slate-400 hover:text-slate-600 font-medium"
              >
                Cancel
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label
                  htmlFor="revision-description"
                  className="block text-xs font-semibold text-slate-700 mb-1"
                >
                  Feedback & Required Adjustments <span className="text-red-500">*</span>
                </label>
                <textarea
                  id="revision-description"
                  rows={4}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Detail the exact sections, copy, styling, or functional tweaks you would like modified..."
                  className="w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-xs text-slate-900 placeholder:text-slate-400 focus:border-slate-800 focus:outline-none focus:ring-1 focus:ring-slate-800 font-normal leading-relaxed"
                />
                <div className="mt-1 flex items-center justify-between text-[11px] text-slate-400">
                  <span>Minimum 10 characters required</span>
                  <span>{description.length} / 5000</span>
                </div>
              </div>

              {/* Attachment Picker */}
              {availableFiles.length > 0 && (
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                    Attach Project Assets / Annotated Mockups (Optional)
                  </label>
                  <p className="text-[11px] text-slate-500 mb-2">
                    Select any previously uploaded project files to associate with this revision request.
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-44 overflow-y-auto pr-1">
                    {availableFiles.map((file) => {
                      const isSelected = selectedAttachmentIds.includes(file.id);
                      return (
                        <div
                          key={file.id}
                          onClick={() => toggleAttachment(file.id)}
                          className={`flex items-center gap-2 rounded-lg border p-2.5 text-xs cursor-pointer transition-colors ${
                            isSelected
                              ? "border-slate-900 bg-slate-100/80 font-medium text-slate-900"
                              : "border-slate-200 bg-white hover:bg-slate-50 text-slate-600"
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => {}}
                            className="h-3.5 w-3.5 rounded border-slate-300 text-slate-900 focus:ring-slate-800"
                          />
                          <Paperclip className="h-3.5 w-3.5 shrink-0 text-slate-400" />
                          <span className="truncate flex-1">{file.original_filename}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  disabled={isSubmitting}
                  className="rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <motion.button
                  {...buttonPressProps}
                  type="submit"
                  disabled={isSubmitting || description.trim().length < 10}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-slate-900 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800 transition-colors disabled:opacity-50 shadow-sm"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      Submitting…
                    </>
                  ) : (
                    <>
                      <Send className="h-3.5 w-3.5" />
                      Submit Revision
                    </>
                  )}
                </motion.button>
              </div>
            </div>
          </motion.form>
        )}
      </AnimatePresence>

      {/* Revision History */}
      <div className="mt-6">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
          Revision History
        </h3>

        {loading ? (
          <div className="flex items-center justify-center py-10 text-slate-400 text-xs">
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
            Loading revisions…
          </div>
        ) : revisions.length === 0 ? (
          <div className="rounded-lg border border-dashed border-slate-200 p-8 text-center">
            <FileCheck className="h-8 w-8 text-slate-300 mx-auto mb-2" />
            <p className="text-xs font-semibold text-slate-600">No revisions requested yet</p>
            <p className="text-[11px] text-slate-400 mt-1 max-w-sm mx-auto">
              Any feedback or iteration requests will be sequentially tracked here alongside developer resolution notes.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {revisions.map((rev) => {
              const statusCfg = STATUS_CONFIG[rev.status] || STATUS_CONFIG.PENDING;
              const StatusIcon = statusCfg.icon;

              return (
                <div
                  key={rev.id}
                  className="rounded-lg border border-slate-200 bg-white p-4.5 shadow-sm transition-all"
                >
                  {/* Revision Top Meta */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">
                        REV #{rev.revision_number}
                      </span>
                      <span className="text-[11px] text-slate-400">
                        {new Date(rev.created_at).toLocaleString("en-IN", {
                          dateStyle: "medium",
                          timeStyle: "short",
                        })}
                      </span>
                    </div>

                    <span
                      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold border ${statusCfg.bg} ${statusCfg.text} ${statusCfg.border}`}
                    >
                      <StatusIcon className="h-3 w-3" />
                      {statusCfg.label}
                    </span>
                  </div>

                  {/* Description */}
                  <div className="mt-3 text-xs text-slate-700 leading-relaxed whitespace-pre-line font-normal">
                    {rev.description}
                  </div>

                  {/* Attachments */}
                  {rev.attachments && rev.attachments.length > 0 && (
                    <div className="mt-3.5 pt-3 border-t border-slate-100">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2">
                        Attached Assets ({rev.attachments.length})
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {rev.attachments.map((att) => (
                          <a
                            key={att.id}
                            href={`/api/v1/projects/${projectId}/files/${att.id}/download`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 rounded border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-medium text-slate-700 hover:bg-slate-100 hover:text-slate-900 transition-colors"
                          >
                            <Paperclip className="h-3 w-3 text-slate-400" />
                            <span className="max-w-[150px] truncate">
                              {att.original_filename}
                            </span>
                            <Download className="h-2.5 w-2.5 text-slate-400 ml-0.5" />
                          </a>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Developer / Studio Resolution Response */}
                  {rev.admin_response && (
                    <div className="mt-3.5 rounded-lg border border-slate-200 bg-slate-50/80 p-3 text-xs">
                      <div className="flex items-center justify-between text-[11px] font-semibold text-slate-700 mb-1">
                        <span>Studio Resolution Response</span>
                        {rev.resolved_at && (
                          <span className="text-[10px] text-slate-400 font-normal">
                            Resolved: {new Date(rev.resolved_at).toLocaleDateString("en-IN")}
                          </span>
                        )}
                      </div>
                      <p className="text-slate-600 leading-relaxed font-normal">
                        {rev.admin_response}
                      </p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
