"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  ExternalLink,
  Laptop,
  Loader2,
  MessageSquare,
  Monitor,
  RefreshCw,
  Send,
  ShieldCheck,
  Smartphone,
  Tablet,
  X,
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { api } from "@/lib/api";
import { ClientBuildPreview, ProjectItem } from "@/types";
import { buttonPressProps } from "@/lib/motion";

export default function ClientBuildPreviewPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params?.id as string;
  const buildId = params?.buildId as string;

  const [preview, setPreview] = useState<ClientBuildPreview | null>(null);
  const [project, setProject] = useState<ProjectItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Viewport Device simulation
  const [device, setDevice] = useState<"desktop" | "tablet" | "mobile">("desktop");

  // Approval Modal
  const [isApproveOpen, setIsApproveOpen] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [isApproving, setIsApproving] = useState(false);

  // Revision Modal
  const [isRevisionOpen, setIsRevisionOpen] = useState(false);
  const [revisionDesc, setRevisionDesc] = useState("");
  const [isSubmittingRev, setIsSubmittingRev] = useState(false);

  const loadData = useCallback(async () => {
    if (!projectId || !buildId) return;
    setLoading(true);
    setError(null);
    try {
      const [prevRes, projRes] = await Promise.all([
        api.get<ClientBuildPreview>(`/projects/${projectId}/builds/${buildId}/preview`),
        api.get<ProjectItem>(`/projects/${projectId}`),
      ]);

      if (prevRes.success && prevRes.data) {
        setPreview(prevRes.data);
      } else {
        setError(prevRes.message || "Unable to load build preview.");
      }

      if (projRes.success && projRes.data) {
        setProject(projRes.data);
      }
    } catch (err: any) {
      setError(err?.message || "This website build is still undergoing internal review and is not ready for client preview.");
    } finally {
      setLoading(false);
    }
  }, [projectId, buildId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleApprove = async () => {
    setIsApproving(true);
    setError(null);
    try {
      const res = await api.post(`/projects/${projectId}/builds/${buildId}/approve`, {
        feedback: feedback.trim() || undefined,
      });

      if (res.success) {
        setSuccess("Website build approved successfully!");
        setIsApproveOpen(false);
        await loadData();
      } else {
        setError(res.message || "Failed to approve website build.");
      }
    } catch (err: any) {
      setError(err?.message || "Failed to submit approval.");
    } finally {
      setIsApproving(false);
    }
  };

  const handleRequestRevision = async () => {
    if (!revisionDesc.trim()) {
      setError("Please describe the modifications you require.");
      return;
    }

    setIsSubmittingRev(true);
    setError(null);
    try {
      const res = await api.post(`/projects/${projectId}/revisions`, {
        description: revisionDesc.trim(),
      });

      if (res.success) {
        setSuccess("Revision request submitted! Our engineering team will review your requested changes.");
        setIsRevisionOpen(false);
        setRevisionDesc("");
        await loadData();
      } else {
        setError(res.message || "Failed to submit revision request.");
      }
    } catch (err: any) {
      setError(err?.message || "Failed to submit revision.");
    } finally {
      setIsSubmittingRev(false);
    }
  };

  const deviceWidthClasses = {
    desktop: "w-full max-w-full",
    tablet: "w-[768px] mx-auto shadow-2xl rounded-t-lg border-x border-t border-slate-700",
    mobile: "w-[375px] mx-auto shadow-2xl rounded-t-lg border-x border-t border-slate-700",
  };

  const sandboxApiUrl = typeof window !== "undefined"
    ? `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/projects/${projectId}/builds/${buildId}/preview-sandbox`
    : "";

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] max-w-[1600px] mx-auto">
      {/* Top Bar Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-white px-4 py-3 shrink-0 shadow-sm">
        <div className="flex items-center gap-3">
          <Link
            href={`/dashboard/projects/${projectId}`}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Project
          </Link>

          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-bold text-slate-900">
                {preview?.project_title || project?.title || "Website Preview"}
              </h1>
              <span className="rounded bg-slate-100 px-2 py-0.5 text-[11px] font-mono font-bold text-slate-700">
                v{preview?.version_number || 1}
              </span>
            </div>
            <p className="text-[11px] text-slate-500">
              Interactive client staging sandbox
            </p>
          </div>
        </div>

        {/* Device Switcher */}
        <div className="hidden md:flex items-center rounded-lg border border-slate-200 bg-slate-100 p-0.5">
          <button
            type="button"
            onClick={() => setDevice("desktop")}
            className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
              device === "desktop"
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Monitor className="h-3.5 w-3.5" />
            Desktop
          </button>
          <button
            type="button"
            onClick={() => setDevice("tablet")}
            className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
              device === "tablet"
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Tablet className="h-3.5 w-3.5" />
            Tablet
          </button>
          <button
            type="button"
            onClick={() => setDevice("mobile")}
            className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
              device === "mobile"
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Smartphone className="h-3.5 w-3.5" />
            Mobile
          </button>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          {preview?.client_approved ? (
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                Approved by You
              </span>
              {project?.status === "PAYMENT_PENDING" && (
                <Link
                  href={`/dashboard/projects/${projectId}`}
                  className="rounded-lg bg-emerald-600 px-3.5 py-1.5 text-xs font-bold text-white hover:bg-emerald-700 transition-colors shadow-sm"
                >
                  Pay Remaining Balance
                </Link>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <motion.div {...buttonPressProps}>
                <button
                  type="button"
                  onClick={() => setIsRevisionOpen(true)}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-sm"
                >
                  <MessageSquare className="h-3.5 w-3.5 text-slate-500" />
                  Request Changes
                </button>
              </motion.div>

              <motion.div {...buttonPressProps}>
                <button
                  type="button"
                  onClick={() => setIsApproveOpen(true)}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3.5 py-1.5 text-xs font-bold text-white hover:bg-emerald-700 transition-colors shadow-sm"
                >
                  <CheckCircle2 className="h-4 w-4" />
                  Approve Website
                </button>
              </motion.div>
            </div>
          )}
        </div>
      </div>

      {/* Notifications */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-2 flex items-center justify-between text-xs text-red-700">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-red-500" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {success && (
        <div className="bg-emerald-50 border-b border-emerald-200 px-4 py-2 flex items-center justify-between text-xs text-emerald-800">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            <span>{success}</span>
          </div>
          <button onClick={() => setSuccess(null)} className="text-emerald-600 hover:text-emerald-800">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Main Sandbox Frame Container */}
      <div className="flex-1 bg-slate-900 p-2 sm:p-4 overflow-auto flex flex-col justify-start">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-400 gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-slate-500" />
            <p className="text-xs font-medium">Loading safe preview sandbox...</p>
          </div>
        ) : (
          <div className={`transition-all duration-300 flex-1 flex flex-col ${deviceWidthClasses[device]}`}>
            {/* Browser top-bar chrome for realism */}
            <div className="bg-slate-800 rounded-t-lg px-3 py-2 flex items-center gap-2 border-b border-slate-700 shrink-0">
              <div className="flex items-center gap-1.5">
                <div className="h-2.5 w-2.5 rounded-full bg-red-500/80" />
                <div className="h-2.5 w-2.5 rounded-full bg-amber-500/80" />
                <div className="h-2.5 w-2.5 rounded-full bg-green-500/80" />
              </div>
              <div className="flex-1 max-w-md mx-auto bg-slate-900/80 rounded px-2.5 py-0.5 text-[11px] font-mono text-slate-400 text-center truncate border border-slate-700/60">
                preview.nexusstudio.app/{project?.project_number?.toLowerCase() || "site"}
              </div>
              <div className="flex items-center gap-1 text-[10px] text-emerald-400 font-medium bg-emerald-950/60 border border-emerald-800/40 rounded px-1.5 py-0.5">
                <ShieldCheck className="h-3 w-3" />
                Safe Sandbox
              </div>
            </div>

            {/* Iframe displaying sandboxed preview with disabled scripts for isolation */}
            <iframe
              src={sandboxApiUrl}
              title="Website Build Sandbox Preview"
              sandbox="allow-same-origin allow-forms"
              className="w-full flex-1 min-h-[500px] bg-white rounded-b-lg border-x border-b border-slate-700 shadow-inner"
            />
          </div>
        )}
      </div>

      {/* Approval Confirmation Modal */}
      <AnimatePresence>
        {isApproveOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 border border-slate-200"
            >
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                  <h3 className="text-base font-bold text-slate-900">Approve Website Build</h3>
                </div>
                <button onClick={() => setIsApproveOpen(false)} className="text-slate-400 hover:text-slate-600">
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="mt-4 space-y-3">
                <p className="text-xs text-slate-600">
                  By approving this website build, you confirm that the generated design, content, and layout meet your requirements.
                </p>
                <p className="text-xs text-slate-600">
                  Following approval, the remaining 50% milestone payment will be unlocked, and your website will be readied for production deployment.
                </p>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Optional Acceptance Feedback
                  </label>
                  <textarea
                    rows={3}
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                    placeholder="Looks great! Ready to launch..."
                    className="w-full rounded-lg border border-slate-300 p-2.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  />
                </div>
              </div>

              <div className="mt-6 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsApproveOpen(false)}
                  disabled={isApproving}
                  className="rounded-lg border border-slate-300 px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleApprove}
                  disabled={isApproving}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-bold text-white hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50"
                >
                  {isApproving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <CheckCircle2 className="h-3.5 w-3.5" />}
                  Confirm Approval
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Revision Request Modal */}
      <AnimatePresence>
        {isRevisionOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6 border border-slate-200"
            >
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5 text-indigo-600" />
                  <h3 className="text-base font-bold text-slate-900">Request Website Changes</h3>
                </div>
                <button onClick={() => setIsRevisionOpen(false)} className="text-slate-400 hover:text-slate-600">
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="mt-4 space-y-3">
                <p className="text-xs text-slate-600">
                  Please provide clear and specific feedback on the changes or adjustments you would like our team to make.
                </p>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Describe Requested Changes *
                  </label>
                  <textarea
                    rows={5}
                    value={revisionDesc}
                    onChange={(e) => setRevisionDesc(e.target.value)}
                    placeholder="e.g. 1. Please update the hero title to...&#10;2. Change the button color to...&#10;3. Add a section for customer testimonials..."
                    className="w-full rounded-lg border border-slate-300 p-2.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div className="mt-6 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsRevisionOpen(false)}
                  disabled={isSubmittingRev}
                  className="rounded-lg border border-slate-300 px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleRequestRevision}
                  disabled={isSubmittingRev}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-700 transition-colors shadow-sm disabled:opacity-50"
                >
                  {isSubmittingRev ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
                  Submit Revision
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
