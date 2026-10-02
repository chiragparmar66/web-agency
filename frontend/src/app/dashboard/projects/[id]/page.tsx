"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ArrowRight, CheckCircle2, Clock, ExternalLink } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { api } from "@/lib/api";
import { ProjectDetail } from "@/types";
import {
  fadeUpVariants,
  staggerContainerVariants,
  cardHoverProps,
  buttonPressProps,
  alertVariants,
} from "@/lib/motion";
import ProjectFiles from "@/components/dashboard/ProjectFiles";
import ProjectRevisions from "@/components/dashboard/ProjectRevisions";
import ProjectBilling from "@/components/dashboard/ProjectBilling";

const STATUS_LABELS: Record<string, string> = {
  LEAD: "Lead",
  NEW: "New",
  REQUIREMENTS_PENDING: "Requirements Pending",
  PENDING_APPROVAL: "Pending Approval",
  BUILDING: "Building Website",
  IN_PROGRESS: "In Progress",
  DESIGN_REVIEW: "Design Review",
  DEVELOPMENT: "Development",
  CLIENT_REVIEW: "Client Review",
  REVISION_REQUESTED: "Revision Requested",
  APPROVED: "Approved",
  PAYMENT_PENDING: "Payment Pending",
  DEPLOYING: "Deploying",
  LIVE: "Live",
  COMPLETED: "Completed",
};

const STATUS_COLORS: Record<string, string> = {
  NEW: "bg-blue-50 text-blue-700",
  REQUIREMENTS_PENDING: "bg-amber-50 text-amber-700",
  PENDING_APPROVAL: "bg-amber-50 text-amber-700",
  BUILDING: "bg-violet-50 text-violet-700",
  IN_PROGRESS: "bg-indigo-50 text-indigo-700",
  DESIGN_REVIEW: "bg-purple-50 text-purple-700",
  DEVELOPMENT: "bg-indigo-50 text-indigo-700",
  CLIENT_REVIEW: "bg-teal-50 text-teal-700",
  REVISION_REQUESTED: "bg-orange-50 text-orange-700",
  APPROVED: "bg-emerald-50 text-emerald-700",
  PAYMENT_PENDING: "bg-yellow-50 text-yellow-800",
  DEPLOYING: "bg-sky-50 text-sky-700",
  LIVE: "bg-green-50 text-green-700",
  COMPLETED: "bg-slate-100 text-slate-500",
};

// Ordered status pipeline
const STATUS_PIPELINE = [
  "NEW",
  "REQUIREMENTS_PENDING",
  "PENDING_APPROVAL",
  "BUILDING",
  "IN_PROGRESS",
  "DESIGN_REVIEW",
  "DEVELOPMENT",
  "CLIENT_REVIEW",
  "APPROVED",
  "PAYMENT_PENDING",
  "DEPLOYING",
  "LIVE",
  "COMPLETED",
];

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params?.id as string;

  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!projectId) return;
    try {
      const res = await api.get<ProjectDetail>(`/projects/${projectId}`);
      if (res.success && res.data) {
        setProject(res.data);
      } else {
        setError("Project not found.");
      }
    } catch {
      setError("Could not load project details.");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-slate-400 text-xs">
        <div className="h-5 w-5 border-2 border-slate-300 border-t-slate-700 rounded-full animate-spin mr-2" />
        Loading project…
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-sm text-red-700">
        {error ?? "Project not found."}
      </div>
    );
  }

  const currentStatusIndex = STATUS_PIPELINE.indexOf(project.status);
  const statusLabel = STATUS_LABELS[project.status] ?? project.status;
  const statusColor = STATUS_COLORS[project.status] ?? "bg-slate-100 text-slate-600";

  return (
    <motion.div
      variants={staggerContainerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-8 max-w-4xl"
    >
      {/* Back */}
      <motion.div variants={fadeUpVariants}>
        <Link
          href="/dashboard/projects"
          className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 font-semibold transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          All Projects
        </Link>
      </motion.div>

      {/* Header */}
      <motion.div
        variants={fadeUpVariants}
        className="flex flex-col sm:flex-row sm:items-start justify-between gap-4"
      >
        <div>
          <p className="text-xs font-mono text-slate-400">{project.project_number}</p>
          <h1 className="mt-0.5 text-2xl font-extrabold text-slate-900 tracking-tight">
            {project.title}
          </h1>
          <p className="text-sm text-slate-500">{project.business_name}</p>
        </div>
        <span
          className={`self-start rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ${statusColor}`}
        >
          {statusLabel}
        </span>
      </motion.div>

      {/* Action Banner based on status */}
      <AnimatePresence>
        {project.status === "NEW" && (
          <motion.div
            variants={alertVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="rounded-lg border border-amber-200 bg-amber-50 p-5 shadow-sm"
          >
            <p className="text-xs font-bold text-amber-800 uppercase tracking-wide mb-1">
              Action Required
            </p>
            <p className="text-sm text-amber-700">
              Please submit your project requirements so our studio team can begin your website.
            </p>
            <motion.div {...buttonPressProps} className="inline-block mt-3">
              <Link
                href={`/dashboard/projects/${project.id}/requirements`}
                className="inline-flex items-center gap-1.5 rounded bg-amber-800 px-4 py-2 text-xs font-semibold text-white hover:bg-amber-900 transition-colors shadow-sm"
              >
                Submit Requirements
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </motion.div>
          </motion.div>
        )}

        {project.status === "CLIENT_REVIEW" && project.preview_url && (
          <motion.div
            variants={alertVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="rounded-lg border border-teal-200 bg-teal-50 p-5 shadow-sm"
          >
            <p className="text-xs font-bold text-teal-800 uppercase tracking-wide mb-1">
              Preview Ready for Review
            </p>
            <p className="text-sm text-teal-700 mb-3">
              Your website preview is ready. Review the staging link below and provide feedback.
            </p>
            <motion.div {...buttonPressProps} className="inline-block">
              <a
                href={project.preview_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 rounded bg-teal-700 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-800 transition-colors shadow-sm"
              >
                <ExternalLink className="h-3.5 w-3.5" />
                View Preview
              </a>
            </motion.div>
          </motion.div>
        )}

        {project.production_url && (project.status === "LIVE" || project.status === "COMPLETED") && (
          <motion.div
            variants={alertVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="rounded-lg border border-green-200 bg-green-50 p-5 shadow-sm"
          >
            <p className="text-xs font-bold text-green-800 uppercase tracking-wide mb-1">
              🎉 Your website is live!
            </p>
            <a
              href={project.production_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm font-semibold text-green-700 hover:underline"
            >
              <ExternalLink className="h-4 w-4" />
              {project.production_url}
            </a>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Status Pipeline with animated progress */}
      <motion.div
        variants={fadeUpVariants}
        className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
      >
        <h2 className="text-sm font-bold text-slate-900 mb-4">Project Progress</h2>
        <div className="overflow-x-auto pb-2">
          <div className="flex items-center min-w-max gap-0">
            {STATUS_PIPELINE.map((s, i) => {
              const isDone = i < currentStatusIndex;
              const isCurrent = i === currentStatusIndex;
              return (
                <div key={s} className="flex items-center">
                  <div className="flex flex-col items-center">
                    <motion.div
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ delay: i * 0.04, duration: 0.25 }}
                      className={`h-7 w-7 rounded-full flex items-center justify-center text-[10px] font-bold border-2 transition-all ${
                        isDone
                          ? "bg-emerald-500 border-emerald-500 text-white"
                          : isCurrent
                          ? "bg-slate-900 border-slate-900 text-white ring-4 ring-slate-100"
                          : "bg-white border-slate-200 text-slate-400"
                      }`}
                    >
                      {isDone ? <CheckCircle2 className="h-4 w-4" /> : i + 1}
                    </motion.div>
                    <p
                      className={`mt-1.5 text-[10px] font-semibold text-center max-w-[64px] leading-tight ${
                        isCurrent ? "text-slate-900 font-bold" : isDone ? "text-emerald-600" : "text-slate-400"
                      }`}
                    >
                      {STATUS_LABELS[s]}
                    </p>
                  </div>
                  {i < STATUS_PIPELINE.length - 1 && (
                    <motion.div
                      initial={{ scaleX: 0 }}
                      animate={{ scaleX: 1 }}
                      transition={{ delay: i * 0.04, duration: 0.3 }}
                      className={`h-0.5 w-8 mx-1 mt-[-16px] origin-left ${
                        i < currentStatusIndex ? "bg-emerald-400" : "bg-slate-200"
                      }`}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </motion.div>

      {/* Two columns: info + timeline */}
      <motion.div variants={fadeUpVariants} className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Project info */}
        <div className="md:col-span-2 space-y-4">
          <div className="rounded-lg border border-slate-200 bg-white p-5 space-y-3 shadow-sm">
            <h2 className="text-sm font-bold text-slate-900">Project Details</h2>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <p className="text-slate-400 font-semibold uppercase tracking-wide text-[10px]">
                  Project Number
                </p>
                <p className="font-mono text-slate-700 mt-0.5">{project.project_number}</p>
              </div>
              <div>
                <p className="text-slate-400 font-semibold uppercase tracking-wide text-[10px]">
                  Status
                </p>
                <p className="text-slate-700 mt-0.5 font-semibold">{statusLabel}</p>
              </div>
              <div>
                <p className="text-slate-400 font-semibold uppercase tracking-wide text-[10px]">
                  Revisions Used
                </p>
                <p className="text-slate-700 mt-0.5">{project.revisions_used}</p>
              </div>
              <div>
                <p className="text-slate-400 font-semibold uppercase tracking-wide text-[10px]">
                  Started
                </p>
                <p className="text-slate-700 mt-0.5">
                  {new Date(project.created_at).toLocaleDateString("en-IN")}
                </p>
              </div>
            </div>
          </div>

          {/* Quick links */}
          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-sm font-bold text-slate-900 mb-3">Quick Actions</h2>
            <div className="flex flex-wrap gap-2">
              <motion.div {...buttonPressProps}>
                <Link
                  href={`/dashboard/projects/${project.id}/requirements`}
                  className="inline-flex items-center gap-1.5 rounded border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
                >
                  View Requirements
                </Link>
              </motion.div>
              {project.preview_url && (
                <motion.div {...buttonPressProps}>
                  <a
                    href={project.preview_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 rounded border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
                  >
                    <ExternalLink className="h-3 w-3" />
                    Preview Link
                  </a>
                </motion.div>
              )}
            </div>
          </div>
        </div>

        {/* Activity timeline */}
        <div>
          <h2 className="text-sm font-bold text-slate-900 mb-3">Activity Timeline</h2>
          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            {!project.activities?.length ? (
              <p className="text-xs text-slate-400 text-center py-4">No activity yet.</p>
            ) : (
              <ol className="relative border-l border-slate-200 pl-4 space-y-4">
                {project.activities.map((a) => (
                  <li key={a.id} className="relative">
                    <div className="absolute -left-[17px] top-0.5 h-3 w-3 rounded-full bg-slate-300 border-2 border-white" />
                    <p className="text-xs font-semibold text-slate-700">
                      {a.action_type.replace(/_/g, " ")}
                    </p>
                    {a.note && (
                      <p className="mt-0.5 text-xs text-slate-500">{a.note}</p>
                    )}
                    <p className="mt-0.5 text-[10px] text-slate-400 flex items-center gap-1">
                      <Clock className="h-2.5 w-2.5" />
                      {new Date(a.created_at).toLocaleString("en-IN")}
                    </p>
                  </li>
                ))}
              </ol>
            )}
          </div>
        </div>
      </motion.div>

      {/* Project Assets & Files */}
      <motion.div variants={fadeUpVariants}>
        <ProjectFiles projectId={project.id} />
      </motion.div>

      {/* Project Billing & Invoices */}
      <motion.div variants={fadeUpVariants}>
        <ProjectBilling
          projectId={project.id}
          projectStatus={project.status}
          onPaymentSuccess={load}
        />
      </motion.div>

      {/* Project Revisions & Feedback */}
      <motion.div variants={fadeUpVariants}>
        <ProjectRevisions
          projectId={project.id}
          projectStatus={project.status}
          revisionsUsed={project.revisions_used}
          onRevisionSubmitted={load}
        />
      </motion.div>
    </motion.div>
  );
}
