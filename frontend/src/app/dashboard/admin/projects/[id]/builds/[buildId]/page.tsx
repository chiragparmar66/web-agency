"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Clock,
  Code2,
  Copy,
  Cpu,
  ExternalLink,
  Eye,
  FileCode,
  FileText,
  FolderTree,
  Loader2,
  RefreshCw,
  Rocket,
  RotateCcw,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  XCircle,
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { api } from "@/lib/api";
import { authStorage } from "@/lib/auth";
import { BuildFileContent, BuildFileItem, BuildReviewDetail, Deployment, DeploymentEligibility, User } from "@/types";
import { buttonPressProps } from "@/lib/motion";

export default function BuildReviewPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params?.id as string;
  const buildId = params?.buildId as string;

  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Review & File Data
  const [review, setReview] = useState<BuildReviewDetail | null>(null);
  const [files, setFiles] = useState<BuildFileItem[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>("index.html");
  const [fileContent, setFileContent] = useState<BuildFileContent | null>(null);
  const [loadingContent, setLoadingContent] = useState(false);

  // Right Panel View Mode: Code or Sandboxed Preview
  const [viewMode, setViewMode] = useState<"code" | "sandbox">("code");
  const [sidebarTab, setSidebarTab] = useState<"files" | "validation" | "specs" | "deploy">("files");

  // Deployment & 5-gate state
  const [eligibility, setEligibility] = useState<DeploymentEligibility | null>(null);
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [isDeployOpen, setIsDeployOpen] = useState(false);
  const [deployProvider, setDeployProvider] = useState<string>("simulated");
  const [deployNotes, setDeployNotes] = useState("");
  const [isDeploying, setIsDeploying] = useState(false);

  // Action Modals
  const [isApproveOpen, setIsApproveOpen] = useState(false);
  const [approveNotes, setApproveNotes] = useState("");
  const [isRejectOpen, setIsRejectOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [isRebuildOpen, setIsRebuildOpen] = useState(false);
  const [rebuildDirective, setRebuildDirective] = useState("");
  const [isActionSubmitting, setIsActionSubmitting] = useState(false);

  // Clipboard copy state
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const currentUser = authStorage.getUser();
    setUser(currentUser);
    if (currentUser && currentUser.role !== "ADMIN" && currentUser.role !== "DEVELOPER") {
      router.push("/dashboard");
    }
  }, [router]);

  const loadReviewData = useCallback(async () => {
    if (!projectId || !buildId) return;
    setLoading(true);
    setError(null);
    try {
      // 1. Fetch review details
      const revRes = await api.get<BuildReviewDetail>(
        `/admin/projects/${projectId}/builds/${buildId}/review`
      );
      if (revRes.success && revRes.data) {
        setReview(revRes.data);
        if (revRes.data.entry_file) {
          setSelectedFile(revRes.data.entry_file);
        }
      }

      // 2. Fetch files metadata list
      const filesRes = await api.get<BuildFileItem[]>(
        `/admin/projects/${projectId}/builds/${buildId}/files?detailed=true`
      );
      if (filesRes.success && filesRes.data) {
        setFiles(filesRes.data);
      }

      // 3. Fetch deployment eligibility and history
      try {
        const [eligRes, depRes] = await Promise.all([
          api.get<DeploymentEligibility>(
            `/admin/projects/${projectId}/builds/${buildId}/deployment-eligibility`
          ),
          api.get<Deployment[]>(`/admin/projects/${projectId}/deployments`),
        ]);
        if (eligRes.success && eligRes.data) setEligibility(eligRes.data);
        if (depRes.success && depRes.data) setDeployments(depRes.data);
      } catch {
        // Non-fatal if deployment endpoint is not yet loaded
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load build review data.");
    } finally {
      setLoading(false);
    }
  }, [projectId, buildId]);

  useEffect(() => {
    if (user && (user.role === "ADMIN" || user.role === "DEVELOPER")) {
      loadReviewData();
    }
  }, [user, loadReviewData]);

  // Load content whenever selectedFile changes
  const loadFileContent = useCallback(
    async (filePath: string) => {
      if (!projectId || !buildId || !filePath) return;
      setLoadingContent(true);
      try {
        const res = await api.get<BuildFileContent>(
          `/admin/projects/${projectId}/builds/${buildId}/files/${encodeURIComponent(filePath)}`
        );
        if (res.success && res.data) {
          setFileContent(res.data);
        }
      } catch (err: any) {
        setFileContent({
          path: filePath,
          file_type: "txt",
          size_bytes: 0,
          content: `// Error loading file: ${err?.message || "Could not read file."}`,
          is_text: true,
          is_truncated: false,
        });
      } finally {
        setLoadingContent(false);
      }
    },
    [projectId, buildId]
  );

  useEffect(() => {
    if (selectedFile) {
      loadFileContent(selectedFile);
    }
  }, [selectedFile, loadFileContent]);

  // Handle Approve Build
  const handleApprove = async () => {
    if (!projectId || !buildId) return;
    setIsActionSubmitting(true);
    setError(null);
    try {
      const res = await api.post(`/admin/projects/${projectId}/builds/${buildId}/approve-review`, {
        notes: approveNotes.trim() || undefined,
      });
      if (res.success) {
        setSuccess("Build has been approved by admin.");
        setIsApproveOpen(false);
        setApproveNotes("");
        await loadReviewData();
      }
    } catch (err: any) {
      setError(err?.message || "Failed to approve build.");
    } finally {
      setIsActionSubmitting(false);
    }
  };

  // Handle Reject Build
  const handleReject = async () => {
    if (!projectId || !buildId || !rejectReason.trim()) return;
    setIsActionSubmitting(true);
    setError(null);
    try {
      const res = await api.post(`/admin/projects/${projectId}/builds/${buildId}/reject-review`, {
        reason: rejectReason.trim(),
      });
      if (res.success) {
        setSuccess("Build marked as rejected.");
        setIsRejectOpen(false);
        setRejectReason("");
        await loadReviewData();
      }
    } catch (err: any) {
      setError(err?.message || "Failed to reject build.");
    } finally {
      setIsActionSubmitting(false);
    }
  };

  // Handle Rebuild Request
  const handleRebuild = async () => {
    if (!projectId || !buildId) return;
    setIsActionSubmitting(true);
    setError(null);
    try {
      const res = await api.post<{ id: string; version_number: number }>(
        `/admin/projects/${projectId}/builds/${buildId}/rebuild`,
        {
          admin_notes: rebuildDirective.trim() || undefined,
        }
      );
      if (res.success && res.data) {
        setSuccess(`Rebuild queued successfully as Build v${res.data.version_number}.`);
        setIsRebuildOpen(false);
        setRebuildDirective("");
        // Navigate to the newly queued build review page
        router.push(`/dashboard/admin/projects/${projectId}/builds/${res.data.id}`);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to trigger rebuild.");
    } finally {
      setIsActionSubmitting(false);
    }
  };

  // Handle Production Deployment
  const handleDeploy = async () => {
    if (!projectId || !buildId) return;
    setIsDeploying(true);
    setError(null);
    try {
      const res = await api.post<Deployment>(
        `/admin/projects/${projectId}/builds/${buildId}/deploy`,
        {
          provider: deployProvider,
          notes: deployNotes.trim() || undefined,
        }
      );
      if (res.success && res.data) {
        setSuccess(`Deployment triggered successfully! Website is live at ${res.data.live_url}`);
        setIsDeployOpen(false);
        setDeployNotes("");
        await loadReviewData();
      } else {
        setError(res.message || "Failed to deploy website.");
      }
    } catch (err: any) {
      setError(err?.message || "Deployment failed. Please verify that all 5 security gates are satisfied.");
    } finally {
      setIsDeploying(false);
    }
  };

  const copyToClipboard = () => {
    if (fileContent?.content) {
      navigator.clipboard.writeText(fileContent.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="flex h-[70vh] items-center justify-center">
        <div className="text-center space-y-3">
          <Loader2 className="mx-auto h-8 w-8 animate-spin text-slate-700" />
          <p className="text-sm font-semibold text-slate-500">Loading Build Artifact Review...</p>
        </div>
      </div>
    );
  }

  if (error && !review) {
    return (
      <div className="mx-auto max-w-2xl py-12 text-center space-y-4">
        <AlertCircle className="mx-auto h-10 w-10 text-red-500" />
        <h2 className="text-lg font-bold text-slate-900">Build Review Unavailable</h2>
        <p className="text-sm text-slate-600">{error}</p>
        <Link
          href="/dashboard/admin"
          className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Studio Console
        </Link>
      </div>
    );
  }

  const reviewStatusColor =
    review?.review_status === "APPROVED"
      ? "bg-emerald-100 text-emerald-800 border-emerald-200"
      : review?.review_status === "REJECTED"
      ? "bg-red-100 text-red-800 border-red-200"
      : "bg-amber-100 text-amber-800 border-amber-200";

  const buildStatusColor =
    review?.status === "COMPLETED"
      ? "bg-emerald-100 text-emerald-800"
      : review?.status === "FAILED"
      ? "bg-red-100 text-red-800"
      : "bg-blue-100 text-blue-800";

  return (
    <div className="space-y-4 pb-12">
      {/* 1. TOP NAVIGATION & HEADER */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 pb-4">
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard/admin"
            className="rounded-lg border border-slate-200 p-2 text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors"
            title="Back to Studio Console"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-lg font-bold text-slate-900">
                {review?.project_title || "Project"} — Build v{review?.version_number}
              </h1>
              <span className={`rounded-full px-2 py-0.5 text-[11px] font-bold ${buildStatusColor}`}>
                {review?.status}
              </span>
              <span className={`rounded-full border px-2 py-0.5 text-[11px] font-bold ${reviewStatusColor}`}>
                Review: {review?.review_status?.replace(/_/g, " ")}
              </span>
              {review?.is_active && (
                <span className="rounded bg-violet-100 text-violet-700 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider">
                  Active Build
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Created: {review ? new Date(review.created_at).toLocaleString("en-IN") : ""}
              {review?.reviewed_at && ` • Reviewed: ${new Date(review.reviewed_at).toLocaleDateString("en-IN")}`}
              {review?.reviewed_by_name && ` by ${review.reviewed_by_name}`}
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {review?.status === "COMPLETED" && review?.review_status !== "APPROVED" && (
            <motion.button
              {...buttonPressProps}
              type="button"
              onClick={() => setIsApproveOpen(true)}
              className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-700 transition-colors shadow-sm"
            >
              <CheckCircle2 className="h-3.5 w-3.5" /> Approve Build
            </motion.button>
          )}

          {review?.review_status !== "REJECTED" && (
            <motion.button
              {...buttonPressProps}
              type="button"
              onClick={() => setIsRejectOpen(true)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-100 transition-colors"
            >
              <XCircle className="h-3.5 w-3.5" /> Reject
            </motion.button>
          )}

          <motion.button
            {...buttonPressProps}
            type="button"
            onClick={() => setIsRebuildOpen(true)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
          >
            <RotateCcw className="h-3.5 w-3.5" /> Request Rebuild
          </motion.button>

          {review?.review_status === "APPROVED" && (
            <motion.button
              {...buttonPressProps}
              type="button"
              onClick={() => {
                setSidebarTab("deploy");
                if (eligibility?.is_eligible) setIsDeployOpen(true);
              }}
              className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-700 transition-colors shadow-sm"
            >
              <Rocket className="h-3.5 w-3.5" /> Deploy to Production
            </motion.button>
          )}
        </div>
      </div>

      {/* Notifications */}
      {success && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-800 flex items-center justify-between">
          <span>{success}</span>
          <button onClick={() => setSuccess(null)} className="text-emerald-600 hover:text-emerald-900 font-bold">
            ×
          </button>
        </div>
      )}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-800 flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-600 hover:text-red-900 font-bold">
            ×
          </button>
        </div>
      )}

      {/* Rejection Notes Banner */}
      {review?.review_status === "REJECTED" && review?.review_notes && (
        <div className="rounded-lg border border-red-200 bg-red-50/70 p-3 text-xs text-red-900 flex items-start gap-2">
          <ShieldAlert className="h-4 w-4 text-red-600 shrink-0 mt-0.5" />
          <div>
            <strong className="block font-bold">Admin Rejection Directive:</strong>
            <p className="mt-0.5 text-red-800">{review.review_notes}</p>
          </div>
        </div>
      )}

      {/* 2. SPLIT WORKSPACE: SIDEBAR & CODE/SANDBOX VIEWER */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        {/* LEFT COLUMN: Files, Validation, & Specs (4 Cols) */}
        <div className="lg:col-span-4 rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          {/* Sidebar Tabs */}
          <div className="flex border-b border-slate-200 bg-slate-50/80">
            <button
              onClick={() => setSidebarTab("files")}
              className={`flex-1 py-2 text-center text-xs font-semibold border-b-2 transition-colors flex items-center justify-center gap-1.5 ${
                sidebarTab === "files"
                  ? "border-slate-900 text-slate-900 bg-white"
                  : "border-transparent text-slate-500 hover:text-slate-700"
              }`}
            >
              <FolderTree className="h-3.5 w-3.5" /> Files ({files.length})
            </button>
            <button
              onClick={() => setSidebarTab("validation")}
              className={`flex-1 py-2 text-center text-xs font-semibold border-b-2 transition-colors flex items-center justify-center gap-1.5 ${
                sidebarTab === "validation"
                  ? "border-slate-900 text-slate-900 bg-white"
                  : "border-transparent text-slate-500 hover:text-slate-700"
              }`}
            >
              <ShieldCheck className="h-3.5 w-3.5" /> Validation ({review?.validation_score ?? 100}%)
            </button>
            <button
              onClick={() => setSidebarTab("specs")}
              className={`flex-1 py-2 text-center text-xs font-semibold border-b-2 transition-colors flex items-center justify-center gap-1.5 ${
                sidebarTab === "specs"
                  ? "border-slate-900 text-slate-900 bg-white"
                  : "border-transparent text-slate-500 hover:text-slate-700"
              }`}
            >
              <Cpu className="h-3.5 w-3.5" /> AI Engine
            </button>
            <button
              onClick={() => setSidebarTab("deploy")}
              className={`flex-1 py-2 text-center text-xs font-semibold border-b-2 transition-colors flex items-center justify-center gap-1.5 ${
                sidebarTab === "deploy"
                  ? "border-slate-900 text-slate-900 bg-white"
                  : "border-transparent text-slate-500 hover:text-slate-700"
              }`}
            >
              <Rocket className="h-3.5 w-3.5" /> Deploy
            </button>
          </div>

          {/* TAB 1: FILE TREE */}
          {sidebarTab === "files" && (
            <div className="divide-y divide-slate-100 max-h-[600px] overflow-y-auto">
              {files.length === 0 ? (
                <div className="p-8 text-center text-xs text-slate-400">No generated files detected in build.</div>
              ) : (
                files.map((file) => {
                  const isSelected = selectedFile === file.path;
                  return (
                    <button
                      key={file.path}
                      onClick={() => setSelectedFile(file.path)}
                      className={`w-full flex items-center justify-between p-2.5 text-left text-xs transition-colors ${
                        isSelected ? "bg-slate-100 font-bold text-slate-900" : "hover:bg-slate-50 text-slate-700"
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate">
                        {file.path.endsWith(".html") ? (
                          <FileCode className="h-4 w-4 text-orange-500 shrink-0" />
                        ) : file.path.endsWith(".css") ? (
                          <FileText className="h-4 w-4 text-blue-500 shrink-0" />
                        ) : file.path.endsWith(".js") ? (
                          <FileCode className="h-4 w-4 text-amber-500 shrink-0" />
                        ) : (
                          <FileText className="h-4 w-4 text-slate-400 shrink-0" />
                        )}
                        <span className="truncate">{file.path}</span>
                      </div>
                      <span className="text-[10px] text-slate-400 shrink-0 ml-2">
                        {(file.size_bytes / 1024).toFixed(1)} KB
                      </span>
                    </button>
                  );
                })
              )}
            </div>
          )}

          {/* TAB 2: VALIDATION FINDINGS */}
          {sidebarTab === "validation" && (
            <div className="p-4 space-y-4 max-h-[600px] overflow-y-auto text-xs">
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide block">
                    Integrity & Security Score
                  </span>
                  <span className="text-xl font-black text-slate-900">{review?.validation_score ?? 100} / 100</span>
                </div>
                <div
                  className={`rounded-full p-2 ${
                    (review?.validation_score ?? 100) >= 90
                      ? "bg-emerald-100 text-emerald-700"
                      : "bg-amber-100 text-amber-700"
                  }`}
                >
                  <ShieldCheck className="h-5 w-5" />
                </div>
              </div>

              <div>
                <span className="font-bold text-slate-800 block mb-2">Automated Validation Findings:</span>
                {(!review?.validation_findings || review.validation_findings.length === 0) ? (
                  <div className="rounded-lg border border-emerald-100 bg-emerald-50/50 p-3 text-emerald-800 flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                    <span>All automated syntax, path containment, and secret scans passed with 0 findings.</span>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {review.validation_findings.map((f, i) => (
                      <div
                        key={i}
                        className={`rounded-lg border p-2.5 text-xs space-y-1 ${
                          f.severity === "ERROR"
                            ? "border-red-200 bg-red-50 text-red-900"
                            : "border-amber-200 bg-amber-50 text-amber-900"
                        }`}
                      >
                        <div className="flex items-center justify-between font-bold text-[11px]">
                          <span>{f.file_path || "Manifest / Global"}</span>
                          <span
                            className={`rounded px-1.5 py-0.2 text-[9px] uppercase ${
                              f.severity === "ERROR" ? "bg-red-200 text-red-800" : "bg-amber-200 text-amber-800"
                            }`}
                          >
                            {f.severity}
                          </span>
                        </div>
                        <p className="text-[11px] leading-relaxed">{f.message}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: AI SPECS & ENGINE METADATA */}
          {sidebarTab === "specs" && (
            <div className="p-4 space-y-4 max-h-[600px] overflow-y-auto text-xs">
              <div>
                <span className="font-bold text-slate-800 block mb-1">Providers Utilized</span>
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 space-y-1.5">
                  {Object.entries(review?.providers_used || {}).map(([stage, prov]) => (
                    <div key={stage} className="flex items-center justify-between text-slate-600">
                      <span className="capitalize font-medium">{stage}:</span>
                      <span className="font-mono font-bold text-slate-900 bg-white px-2 py-0.5 rounded border border-slate-200 text-[10px]">
                        {prov}
                      </span>
                    </div>
                  ))}
                  {Object.keys(review?.providers_used || {}).length === 0 && (
                    <span className="text-slate-400 italic">No provider logs recorded.</span>
                  )}
                </div>
              </div>

              {review?.spec_summary && (
                <div>
                  <span className="font-bold text-slate-800 block mb-1">Analysis Specification</span>
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-[11px] text-slate-700 leading-relaxed space-y-1">
                    <p>
                      <strong>Website Type:</strong> {review.spec_summary.website_type || "Custom Static Site"}
                    </p>
                    <p>
                      <strong>Target Audience:</strong> {review.spec_summary.target_audience || "General Audience"}
                    </p>
                    {review.spec_summary.summary && (
                      <p className="mt-1 pt-1 border-t border-slate-200">{review.spec_summary.summary}</p>
                    )}
                  </div>
                </div>
              )}

              {review?.admin_notes && (
                <div>
                  <span className="font-bold text-slate-800 block mb-1">Admin Build Directives</span>
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-2.5 text-[11px] text-slate-600 italic">
                    &ldquo;{review.admin_notes}&rdquo;
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: DEPLOYMENT GATES & CONTROLS */}
          {sidebarTab === "deploy" && (
            <div className="p-4 space-y-4 max-h-[600px] overflow-y-auto text-xs">
              <div>
                <span className="font-bold text-slate-800 block mb-1">Production Gate Verification</span>
                <p className="text-[11px] text-slate-500 mb-3">
                  All 5 security gates are evaluated authoritatively before live deployment:
                </p>

                <div className="space-y-2 rounded-lg border border-slate-200 bg-slate-50 p-3">
                  {/* Gate 1 */}
                  <div className="flex items-center justify-between">
                    <span className="text-slate-700 font-medium">1. Build Status</span>
                    {eligibility?.build_completed ? (
                      <span className="inline-flex items-center gap-1 text-emerald-700 font-bold text-[11px]">
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" /> Completed
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-red-700 font-bold text-[11px]">
                        <XCircle className="h-3.5 w-3.5 text-red-500" /> Not Completed
                      </span>
                    )}
                  </div>

                  {/* Gate 2 */}
                  <div className="flex items-center justify-between">
                    <span className="text-slate-700 font-medium">2. Admin Review</span>
                    {eligibility?.admin_approved ? (
                      <span className="inline-flex items-center gap-1 text-emerald-700 font-bold text-[11px]">
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" /> Approved
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-red-700 font-bold text-[11px]">
                        <XCircle className="h-3.5 w-3.5 text-red-500" /> Pending Review
                      </span>
                    )}
                  </div>

                  {/* Gate 3 */}
                  <div className="flex items-center justify-between">
                    <span className="text-slate-700 font-medium">3. Client Approval</span>
                    {eligibility?.client_approved ? (
                      <span className="inline-flex items-center gap-1 text-emerald-700 font-bold text-[11px]">
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" /> Client Approved
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-amber-700 font-bold text-[11px]">
                        <Clock className="h-3.5 w-3.5 text-amber-600" /> Awaiting Client
                      </span>
                    )}
                  </div>

                  {/* Gate 4 */}
                  <div className="flex items-center justify-between">
                    <span className="text-slate-700 font-medium">4. Final Payment</span>
                    {eligibility?.final_payment_cleared ? (
                      <span className="inline-flex items-center gap-1 text-emerald-700 font-bold text-[11px]">
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" /> 100% Cleared
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-amber-700 font-bold text-[11px]">
                        <Clock className="h-3.5 w-3.5 text-amber-600" /> ₹{eligibility?.remaining_balance_inr?.toFixed(2) || "0"} Due
                      </span>
                    )}
                  </div>

                  {/* Gate 5 */}
                  <div className="flex items-center justify-between">
                    <span className="text-slate-700 font-medium">5. Artifact Health</span>
                    {eligibility?.artifact_available ? (
                      <span className="inline-flex items-center gap-1 text-emerald-700 font-bold text-[11px]">
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" /> Validated
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-red-700 font-bold text-[11px]">
                        <XCircle className="h-3.5 w-3.5 text-red-500" /> Missing / Invalid
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Blockers Callout */}
              {eligibility && !eligibility.is_eligible && eligibility.blockers.length > 0 && (
                <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-amber-900 text-[11px] space-y-1">
                  <div className="flex items-center gap-1 font-bold text-amber-900">
                    <AlertCircle className="h-3.5 w-3.5 text-amber-600" />
                    Pending Gate Prerequisites:
                  </div>
                  <ul className="list-disc pl-4 space-y-0.5 text-amber-800">
                    {eligibility.blockers.map((b, idx) => (
                      <li key={idx}>{b}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Deploy Trigger Button */}
              {eligibility?.is_eligible ? (
                <div className="pt-2">
                  <button
                    type="button"
                    onClick={() => setIsDeployOpen(true)}
                    className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 py-2.5 px-4 text-xs font-bold text-white hover:bg-indigo-700 transition-colors shadow-sm"
                  >
                    <Rocket className="h-4 w-4" /> Trigger Production Deployment
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  disabled
                  className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-slate-100 py-2.5 px-4 text-xs font-bold text-slate-400 cursor-not-allowed border border-slate-200"
                >
                  <Rocket className="h-4 w-4" /> Deployment Locked (Prerequisites Pending)
                </button>
              )}

              {/* Deployment History */}
              {deployments.length > 0 && (
                <div className="pt-4 border-t border-slate-200 space-y-2">
                  <span className="font-bold text-slate-800 block text-xs">Deployment History</span>
                  <div className="space-y-2">
                    {deployments.map((d) => (
                      <div key={d.id} className="rounded-lg border border-slate-200 p-2.5 bg-white text-[11px] space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-900">
                            Build v{d.version_number} via {d.provider}
                          </span>
                          <span
                            className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase ${
                              d.status === "DEPLOYED"
                                ? "bg-emerald-100 text-emerald-800"
                                : d.status === "DEPLOYING"
                                ? "bg-sky-100 text-sky-800"
                                : "bg-red-100 text-red-800"
                            }`}
                          >
                            {d.status}
                          </span>
                        </div>
                        {d.live_url && (
                          <a
                            href={d.live_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-indigo-600 hover:underline flex items-center gap-1 font-medium truncate"
                          >
                            <ExternalLink className="h-3 w-3 shrink-0" />
                            {d.live_url}
                          </a>
                        )}
                        {d.error_message && (
                          <p className="text-red-600 truncate">{d.error_message}</p>
                        )}
                        <p className="text-[10px] text-slate-400">
                          {new Date(d.created_at).toLocaleString("en-IN")}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* RIGHT COLUMN: CODE VIEWER OR SAFE SANDBOX (8 Cols) */}
        <div className="lg:col-span-8 rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden flex flex-col">
          {/* Viewer Toolbar */}
          <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 p-3">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-slate-900 bg-white border border-slate-200 px-2.5 py-1 rounded">
                {selectedFile}
              </span>
              {fileContent?.is_truncated && (
                <span className="text-[10px] rounded bg-amber-100 text-amber-800 px-2 py-0.5 font-bold">
                  File truncated (1MB limit)
                </span>
              )}
            </div>

            <div className="flex items-center gap-2">
              {/* Toggle Code vs Sandbox */}
              <div className="flex rounded-lg border border-slate-200 bg-white p-0.5 text-xs font-semibold">
                <button
                  type="button"
                  onClick={() => setViewMode("code")}
                  className={`inline-flex items-center gap-1 rounded-md px-2.5 py-1 transition-colors ${
                    viewMode === "code" ? "bg-slate-900 text-white" : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <Code2 className="h-3.5 w-3.5" /> Code
                </button>
                <button
                  type="button"
                  onClick={() => setViewMode("sandbox")}
                  className={`inline-flex items-center gap-1 rounded-md px-2.5 py-1 transition-colors ${
                    viewMode === "sandbox" ? "bg-slate-900 text-white" : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <Eye className="h-3.5 w-3.5" /> Sandbox View
                </button>
              </div>

              {viewMode === "code" && fileContent?.content && (
                <button
                  type="button"
                  onClick={copyToClipboard}
                  className="rounded-lg border border-slate-200 bg-white p-1.5 text-slate-600 hover:text-slate-900 transition-colors"
                  title="Copy code"
                >
                  {copied ? <CheckCircle2 className="h-4 w-4 text-emerald-600" /> : <Copy className="h-4 w-4" />}
                </button>
              )}
            </div>
          </div>

          {/* VIEWER CONTENT */}
          <div className="min-h-[550px] max-h-[700px] overflow-auto bg-slate-950 text-slate-100">
            {loadingContent ? (
              <div className="flex h-64 items-center justify-center text-slate-400">
                <Loader2 className="h-6 w-6 animate-spin mr-2" /> Loading content...
              </div>
            ) : viewMode === "code" ? (
              fileContent?.is_text ? (
                <pre className="p-4 text-xs font-mono leading-relaxed whitespace-pre overflow-x-auto text-slate-200">
                  <code>{fileContent.content}</code>
                </pre>
              ) : (
                <div className="p-12 text-center text-xs text-slate-400 space-y-2">
                  <FileText className="mx-auto h-8 w-8 text-slate-600" />
                  <p>Binary or non-text file ({fileContent?.file_type}).</p>
                  <p className="text-[11px] text-slate-500">Size: {fileContent?.size_bytes} bytes</p>
                </div>
              )
            ) : (
              /* SAFE SANDBOX PREVIEW */
              <div className="h-[650px] w-full flex flex-col bg-white">
                <div className="bg-amber-50 border-b border-amber-200 px-3 py-1.5 text-[11px] text-amber-800 flex items-center justify-between shrink-0">
                  <span className="flex items-center gap-1 font-semibold">
                    <Shield className="h-3.5 w-3.5 text-amber-600" /> Safe Sandbox Preview: JavaScript execution is disabled
                    for administrative security.
                  </span>
                  <span className="text-[10px] text-amber-700">Strict CSP active</span>
                </div>
                <iframe
                  src={`/api/v1/admin/projects/${projectId}/builds/${buildId}/sandbox-view?path=${encodeURIComponent(
                    selectedFile
                  )}`}
                  sandbox="allow-same-origin"
                  title="Nexus Studio Safe Sandbox Preview"
                  className="h-full w-full border-0 bg-white"
                />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 3. ACTION MODALS */}
      {/* A. APPROVE MODAL */}
      <AnimatePresence>
        {isApproveOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-md rounded-xl bg-white p-5 shadow-xl border border-slate-200 text-xs space-y-4"
            >
              <div className="flex items-center gap-2 text-emerald-700 font-bold text-sm">
                <CheckCircle2 className="h-5 w-5" /> Confirm Build Approval
              </div>
              <p className="text-slate-600">
                You are approving <strong>Build v{review?.version_number}</strong> for project{" "}
                <strong>{review?.project_title}</strong>. This indicates you have inspected the generated artifacts and
                deemed them ready for client presentation.
              </p>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Approval Notes (Optional)</label>
                <textarea
                  rows={2}
                  value={approveNotes}
                  onChange={(e) => setApproveNotes(e.target.value)}
                  placeholder="e.g., Code reviewed, responsive layout verified."
                  className="w-full rounded-md border border-slate-300 p-2 text-slate-900 focus:outline-none focus:border-slate-900"
                />
              </div>
              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsApproveOpen(false)}
                  className="rounded-md border border-slate-300 px-3 py-1.5 font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <motion.button
                  {...buttonPressProps}
                  type="button"
                  onClick={handleApprove}
                  disabled={isActionSubmitting}
                  className="inline-flex items-center gap-1.5 rounded-md bg-emerald-600 px-4 py-1.5 font-semibold text-white hover:bg-emerald-700 transition-colors disabled:opacity-50"
                >
                  {isActionSubmitting && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                  Confirm Approval
                </motion.button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* B. REJECT MODAL */}
      <AnimatePresence>
        {isRejectOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-md rounded-xl bg-white p-5 shadow-xl border border-slate-200 text-xs space-y-4"
            >
              <div className="flex items-center gap-2 text-red-700 font-bold text-sm">
                <XCircle className="h-5 w-5" /> Reject Build
              </div>
              <p className="text-slate-600">
                Please provide a mandatory reason for rejecting this build artifact. This reason will be recorded in the
                project audit history.
              </p>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Rejection Reason <span className="text-red-500">*</span>
                </label>
                <textarea
                  rows={3}
                  required
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="e.g., Color palette does not match brand assets; missing contact form styling."
                  className="w-full rounded-md border border-slate-300 p-2 text-slate-900 focus:outline-none focus:border-slate-900"
                />
              </div>
              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsRejectOpen(false)}
                  className="rounded-md border border-slate-300 px-3 py-1.5 font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <motion.button
                  {...buttonPressProps}
                  type="button"
                  onClick={handleReject}
                  disabled={isActionSubmitting || rejectReason.trim().length < 3}
                  className="inline-flex items-center gap-1.5 rounded-md bg-red-600 px-4 py-1.5 font-semibold text-white hover:bg-red-700 transition-colors disabled:opacity-50"
                >
                  {isActionSubmitting && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                  Confirm Rejection
                </motion.button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* C. REBUILD MODAL */}
      <AnimatePresence>
        {isRebuildOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-md rounded-xl bg-white p-5 shadow-xl border border-slate-200 text-xs space-y-4"
            >
              <div className="flex items-center gap-2 text-slate-900 font-bold text-sm">
                <RotateCcw className="h-5 w-5 text-violet-600" /> Request Rebuild (v{(review?.version_number || 1) + 1})
              </div>
              <p className="text-slate-600">
                This will queue a new versioned build run using the existing project context while safely preserving all
                previous artifacts and review history.
              </p>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">New Build Directives (Optional)</label>
                <textarea
                  rows={3}
                  value={rebuildDirective}
                  onChange={(e) => setRebuildDirective(e.target.value)}
                  placeholder="e.g., Use lighter typography, ensure mobile nav is prominent."
                  className="w-full rounded-md border border-slate-300 p-2 text-slate-900 focus:outline-none focus:border-slate-900"
                />
              </div>
              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsRebuildOpen(false)}
                  className="rounded-md border border-slate-300 px-3 py-1.5 font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <motion.button
                  {...buttonPressProps}
                  type="button"
                  onClick={handleRebuild}
                  disabled={isActionSubmitting}
                  className="inline-flex items-center gap-1.5 rounded-md bg-violet-600 px-4 py-1.5 font-semibold text-white hover:bg-violet-700 transition-colors disabled:opacity-50"
                >
                  {isActionSubmitting && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                  Queue Rebuild
                </motion.button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* D. DEPLOYMENT CONFIRMATION MODAL */}
      <AnimatePresence>
        {isDeployOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-md rounded-xl bg-white p-5 shadow-xl border border-slate-200 text-xs space-y-4"
            >
              <div className="flex items-center gap-2 text-slate-900 font-bold text-sm">
                <Rocket className="h-5 w-5 text-indigo-600" /> Deploy to Production
              </div>
              <p className="text-slate-600 leading-relaxed">
                All 5 security prerequisites are verified. Deploying build v{review?.version_number} will publish artifacts and update the project production URL.
              </p>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Deployment Provider</label>
                <select
                  value={deployProvider}
                  onChange={(e) => setDeployProvider(e.target.value)}
                  className="w-full rounded-md border border-slate-300 p-2 text-slate-900 bg-white focus:outline-none focus:border-slate-900"
                >
                  <option value="simulated">Simulated Local/Staging Provider</option>
                  <option value="vercel">Vercel Production</option>
                  <option value="netlify">Netlify Production</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Deployment Notes (Optional)</label>
                <input
                  type="text"
                  value={deployNotes}
                  onChange={(e) => setDeployNotes(e.target.value)}
                  placeholder="e.g. Production launch v1.0"
                  className="w-full rounded-md border border-slate-300 p-2 text-slate-900 focus:outline-none focus:border-slate-900"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsDeployOpen(false)}
                  disabled={isDeploying}
                  className="rounded-md border border-slate-300 px-3 py-1.5 font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <motion.button
                  {...buttonPressProps}
                  type="button"
                  onClick={handleDeploy}
                  disabled={isDeploying}
                  className="inline-flex items-center gap-1.5 rounded-md bg-indigo-600 px-4 py-1.5 font-semibold text-white hover:bg-indigo-700 transition-colors disabled:opacity-50"
                >
                  {isDeploying ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Rocket className="h-3.5 w-3.5" />}
                  Launch Deployment
                </motion.button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
