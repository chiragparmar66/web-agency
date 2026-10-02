"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  Download,
  FileText,
  Image as ImageIcon,
  Loader2,
  Trash2,
  UploadCloud,
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { api, ApiError } from "@/lib/api";
import { FileCategory, ProjectFileItem } from "@/types";
import { alertVariants, buttonPressProps } from "@/lib/motion";

interface ProjectFilesProps {
  projectId: string;
}

const CATEGORY_OPTIONS: { value: FileCategory; label: string; hint: string }[] = [
  { value: "LOGO", label: "Logo & Brand Mark", hint: "PNG, JPG, WEBP, GIF (Max 5MB)" },
  { value: "IMAGE", label: "Content Image / Photo", hint: "PNG, JPG, WEBP, GIF (Max 5MB)" },
  { value: "DOCUMENT", label: "Project Spec / Document", hint: "PDF, DOCX (Max 10MB)" },
  { value: "BRAND_ASSET", label: "General Brand Asset", hint: "PNG, JPG, WEBP, GIF, PDF, DOCX" },
];

const CATEGORY_BADGES: Record<FileCategory, string> = {
  LOGO: "bg-blue-50 text-blue-700 border-blue-200",
  IMAGE: "bg-emerald-50 text-emerald-700 border-emerald-200",
  DOCUMENT: "bg-amber-50 text-amber-700 border-amber-200",
  BRAND_ASSET: "bg-purple-50 text-purple-700 border-purple-200",
  REVISION_ATTACHMENT: "bg-orange-50 text-orange-700 border-orange-200",
  PREVIEW_SCREENSHOT: "bg-slate-50 text-slate-700 border-slate-200",
};

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export default function ProjectFiles({ projectId }: ProjectFilesProps) {
  const [files, setFiles] = useState<ProjectFileItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<FileCategory>("LOGO");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadFiles = useCallback(async () => {
    try {
      const res = await api.get<ProjectFileItem[]>(`/projects/${projectId}/files`);
      if (res.success && res.data) {
        setFiles(res.data);
      }
    } catch {
      // Non-fatal if project files cannot be loaded initially
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId) {
      loadFiles();
    }
  }, [projectId, loadFiles]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    setSuccess(null);
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const ext = file.name.split(".").pop()?.toLowerCase();

      // Quick client-side check
      if (selectedCategory === "LOGO" || selectedCategory === "IMAGE") {
        if (!["png", "jpg", "jpeg", "webp", "gif"].includes(ext || "")) {
          setError(`Category '${selectedCategory}' requires an image file (PNG, JPG, WEBP, GIF).`);
          return;
        }
        if (file.size > 5 * 1024 * 1024) {
          setError("Image file size exceeds the 5 MB limit.");
          return;
        }
      } else if (selectedCategory === "DOCUMENT") {
        if (!["pdf", "docx"].includes(ext || "")) {
          setError("Category 'DOCUMENT' requires a PDF or DOCX file.");
          return;
        }
        if (file.size > 10 * 1024 * 1024) {
          setError("Document file size exceeds the 10 MB limit.");
          return;
        }
      }

      setSelectedFile(file);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setError("Please choose a file to upload.");
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(null);

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("file_category", selectedCategory);

    try {
      const res = await api.upload<ProjectFileItem>(
        `/projects/${projectId}/files`,
        formData
      );
      if (res.success && res.data) {
        setSuccess(`"${res.data.original_filename}" uploaded and secured successfully.`);
        setSelectedFile(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
        await loadFiles();
      } else {
        setError(res.message || "Failed to upload file.");
      }
    } catch (err: any) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Network error while uploading asset. Please try again.");
      }
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (fileItem: ProjectFileItem) => {
    setDownloadingId(fileItem.id);
    setError(null);
    try {
      await api.downloadBlob(
        `/projects/${projectId}/files/${fileItem.id}/download`,
        fileItem.original_filename
      );
    } catch (err: any) {
      setError(err.message || "Unable to download asset.");
    } finally {
      setDownloadingId(null);
    }
  };

  const handleDelete = async (fileItem: ProjectFileItem) => {
    if (!confirm(`Are you sure you want to delete "${fileItem.original_filename}"?`)) {
      return;
    }

    setDeletingId(fileItem.id);
    setError(null);
    setSuccess(null);

    try {
      const res = await api.delete(`/projects/${projectId}/files/${fileItem.id}`);
      if (res.success) {
        setSuccess(`Deleted "${fileItem.original_filename}".`);
        setFiles((prev) => prev.filter((f) => f.id !== fileItem.id));
      } else {
        setError(res.message || "Could not delete asset.");
      }
    } catch (err: any) {
      setError(err.message || "Unable to delete asset.");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
        <div>
          <h2 className="text-base font-bold text-slate-900">Project Files & Brand Assets</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Secure asset repository. Upload your logos, photos, and project documentation.
          </p>
        </div>
        <span className="text-[11px] font-semibold text-slate-400 bg-slate-50 border border-slate-200 rounded px-2.5 py-1 self-start sm:self-auto">
          {files.length} / 50 Files
        </span>
      </div>

      {/* Upload Box */}
      <form onSubmit={handleUpload} className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Asset Category <span className="text-rose-500">*</span>
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => {
                setSelectedCategory(e.target.value as FileCategory);
                setSelectedFile(null);
                if (fileInputRef.current) fileInputRef.current.value = "";
              }}
              className="w-full rounded border border-slate-300 px-3 py-2 text-xs font-medium text-slate-800 bg-white focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600"
            >
              {CATEGORY_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <p className="text-[10px] text-slate-400 mt-1">
              {CATEGORY_OPTIONS.find((c) => c.value === selectedCategory)?.hint}
            </p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Select File <span className="text-rose-500">*</span>
            </label>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".png,.jpg,.jpeg,.webp,.gif,.pdf,.docx"
              className="w-full rounded border border-slate-300 px-3 py-1.5 text-xs text-slate-600 file:mr-3 file:py-1 file:px-2.5 file:rounded file:border-0 file:text-[11px] file:font-semibold file:bg-slate-100 file:text-slate-700 hover:file:bg-slate-200 focus:outline-none"
            />
            {selectedFile && (
              <p className="text-[11px] text-slate-600 font-medium mt-1 truncate">
                Selected: {selectedFile.name} ({formatBytes(selectedFile.size)})
              </p>
            )}
          </div>
        </div>

        <div className="flex justify-end">
          <motion.div {...buttonPressProps}>
            <button
              type="submit"
              disabled={uploading || !selectedFile}
              className="inline-flex items-center gap-2 rounded bg-slate-900 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800 disabled:opacity-50 transition-colors shadow-sm"
            >
              {uploading ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  <span>Securing & Uploading...</span>
                </>
              ) : (
                <>
                  <UploadCloud className="h-3.5 w-3.5" />
                  <span>Upload Asset</span>
                </>
              )}
            </button>
          </motion.div>
        </div>
      </form>

      {/* Notifications */}
      <AnimatePresence>
        {error && (
          <motion.div
            variants={alertVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="rounded border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 flex items-start gap-2"
          >
            <AlertCircle className="h-4 w-4 shrink-0 text-rose-600 mt-0.5" />
            <span>{error}</span>
          </motion.div>
        )}
        {success && (
          <motion.div
            variants={alertVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="rounded border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-800 flex items-start gap-2"
          >
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600 mt-0.5" />
            <span>{success}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Files List */}
      <div>
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
          Uploaded Assets
        </h3>

        {loading ? (
          <div className="py-8 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin text-slate-600" />
            <span>Loading assets...</span>
          </div>
        ) : files.length === 0 ? (
          <div className="rounded-lg border border-dashed border-slate-200 p-8 text-center bg-slate-50/50">
            <UploadCloud className="h-8 w-8 text-slate-300 mx-auto mb-2" />
            <p className="text-xs font-semibold text-slate-700">No files or assets uploaded yet.</p>
            <p className="text-[11px] text-slate-400 mt-1 max-w-sm mx-auto">
              Upload your high-resolution logos, brand guidelines, photo assets, or PDF project briefs above.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100 rounded-lg border border-slate-200 overflow-hidden">
            {files.map((file) => {
              const isImage = file.mime_type.startsWith("image/");
              const badgeClass = CATEGORY_BADGES[file.file_category] || "bg-slate-50 text-slate-700 border-slate-200";

              return (
                <div
                  key={file.id}
                  className="flex items-center justify-between p-3.5 hover:bg-slate-50/80 transition-colors gap-3"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-slate-100 text-slate-600">
                      {isImage ? (
                        <ImageIcon className="h-4 w-4" />
                      ) : (
                        <FileText className="h-4 w-4" />
                      )}
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-slate-900 truncate">
                        {file.original_filename}
                      </p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span
                          className={`rounded border px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider ${badgeClass}`}
                        >
                          {file.file_category.replace(/_/g, " ")}
                        </span>
                        <span className="text-[10px] text-slate-400">
                          {formatBytes(file.file_size_bytes)}
                        </span>
                        <span className="text-[10px] text-slate-300">&bull;</span>
                        <span className="text-[10px] text-slate-400">
                          {new Date(file.created_at).toLocaleDateString("en-IN")}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      type="button"
                      onClick={() => handleDownload(file)}
                      disabled={downloadingId === file.id}
                      title="Download Asset"
                      className="inline-flex items-center gap-1 rounded border border-slate-200 bg-white p-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 hover:text-slate-900 disabled:opacity-50 transition-colors shadow-2xs"
                    >
                      {downloadingId === file.id ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Download className="h-3.5 w-3.5 text-slate-600" />
                      )}
                    </button>

                    <button
                      type="button"
                      onClick={() => handleDelete(file)}
                      disabled={deletingId === file.id}
                      title="Delete Asset"
                      className="inline-flex items-center rounded border border-slate-200 bg-white p-1.5 text-xs font-semibold text-rose-600 hover:bg-rose-50 hover:border-rose-200 disabled:opacity-50 transition-colors shadow-2xs"
                    >
                      {deletingId === file.id ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Trash2 className="h-3.5 w-3.5" />
                      )}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
