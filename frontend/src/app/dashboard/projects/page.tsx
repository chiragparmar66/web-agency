"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, FolderOpen, Plus } from "lucide-react";
import { motion } from "motion/react";
import { api } from "@/lib/api";
import { ProjectItem } from "@/types";
import { fadeUpVariants, cardHoverProps, staggerContainerVariants } from "@/lib/motion";

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

export default function ProjectsListPage() {
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get<ProjectItem[]>("/projects");
        if (res.success && res.data) {
          setProjects(res.data);
        } else {
          setError("Could not load projects.");
        }
      } catch {
        setError("Network error. Please try again.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-slate-400 text-xs">
        <div className="h-5 w-5 border-2 border-slate-300 border-t-slate-700 rounded-full animate-spin mr-2" />
        Loading projects…
      </div>
    );
  }

  return (
    <motion.div
      variants={staggerContainerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Header */}
      <motion.div
        variants={fadeUpVariants}
        className="flex flex-col sm:flex-row sm:items-center justify-between gap-4"
      >
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">My Projects</h1>
          <p className="mt-1 text-sm text-slate-500">
            All your commissioned website projects.
          </p>
        </div>
        <Link
          href="/dashboard/projects/new"
          className="inline-flex items-center gap-2 rounded bg-slate-900 px-4 py-2.5 text-xs font-semibold text-white hover:bg-slate-800 transition-colors"
        >
          <Plus className="h-3.5 w-3.5" />
          New Project
        </Link>
      </motion.div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {!loading && !error && !projects.length && (
        <motion.div
          variants={fadeUpVariants}
          className="rounded-lg border border-dashed border-slate-300 bg-white p-12 text-center"
        >
          <FolderOpen className="h-10 w-10 text-slate-300 mx-auto mb-4" />
          <h2 className="text-sm font-bold text-slate-800">No projects yet</h2>
          <p className="text-xs text-slate-500 mt-1 max-w-xs mx-auto">
            Commission your first website project and our studio team will review your requirements within 24 hours.
          </p>
          <Link
            href="/dashboard/projects/new"
            className="mt-5 inline-flex items-center gap-2 rounded bg-slate-900 px-5 py-2.5 text-xs font-semibold text-white hover:bg-slate-800 transition-colors"
          >
            <Plus className="h-3.5 w-3.5" />
            Start Your First Project
          </Link>
        </motion.div>
      )}

      {/* Project list */}
      {projects.length > 0 && (
        <motion.div variants={staggerContainerVariants} className="space-y-3">
          {projects.map((project) => {
            const statusLabel = STATUS_LABELS[project.status] ?? project.status;
            const statusColor = STATUS_COLORS[project.status] ?? "bg-slate-100 text-slate-600";
            return (
              <motion.div
                key={project.id}
                variants={fadeUpVariants}
                {...cardHoverProps}
              >
                <Link
                  href={`/dashboard/projects/${project.id}`}
                  className="flex items-center gap-4 rounded-lg border border-slate-200 bg-white p-5 hover:shadow-md transition-shadow block"
                >
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded bg-slate-900 text-white font-bold text-xs">
                    {project.title.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="text-sm font-bold text-slate-900 truncate">{project.title}</p>
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${statusColor}`}
                      >
                        {statusLabel}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">{project.business_name}</p>
                    <p className="text-[10px] text-slate-400 mt-0.5 font-mono">
                      {project.project_number}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-1 shrink-0">
                    <p className="text-[10px] text-slate-400">
                      {new Date(project.updated_at).toLocaleDateString("en-IN")}
                    </p>
                    <ArrowRight className="h-4 w-4 text-slate-300" />
                  </div>
                </Link>
              </motion.div>
            );
          })}
        </motion.div>
      )}
    </motion.div>
  );
}
