"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Clock, FolderOpen, Plus, TrendingUp } from "lucide-react";
import { motion } from "motion/react";
import { api } from "@/lib/api";
import { DashboardSummary, ProjectItem, ActivityItem } from "@/types";
import {
  fadeUpVariants,
  staggerContainerVariants,
  cardHoverProps,
  buttonPressProps,
} from "@/lib/motion";

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
  LEAD: "bg-slate-100 text-slate-600",
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

function ProjectCard({ project }: { project: ProjectItem }) {
  const statusLabel = STATUS_LABELS[project.status] ?? project.status;
  const statusColor =
    STATUS_COLORS[project.status] ?? "bg-slate-100 text-slate-600";

  return (
    <motion.div variants={fadeUpVariants} {...cardHoverProps}>
      <Link
        href={`/dashboard/projects/${project.id}`}
        className="block rounded-lg border border-slate-200 bg-white p-5 hover:border-slate-300 hover:shadow-md transition-shadow"
      >
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="min-w-0">
            <p className="text-xs font-mono text-slate-400">{project.project_number}</p>
            <h3 className="mt-0.5 text-sm font-bold text-slate-900 truncate">{project.title}</h3>
            <p className="text-xs text-slate-500 truncate">{project.business_name}</p>
          </div>
          <span
            className={`shrink-0 rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${statusColor}`}
          >
            {statusLabel}
          </span>
        </div>
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>Started {new Date(project.created_at).toLocaleDateString("en-IN")}</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </div>
      </Link>
    </motion.div>
  );
}

function ActivityFeed({ activities }: { activities: ActivityItem[] }) {
  if (!activities.length) {
    return (
      <p className="text-xs text-slate-400 py-4 text-center">No recent activity.</p>
    );
  }
  return (
    <motion.ol
      variants={staggerContainerVariants}
      initial="hidden"
      animate="visible"
      className="relative border-l border-slate-200 pl-4 space-y-4"
    >
      {activities.map((a) => (
        <motion.li key={a.id} variants={fadeUpVariants} className="relative">
          <div className="absolute -left-[17px] top-0.5 h-3 w-3 rounded-full bg-slate-300 border-2 border-white" />
          <p className="text-xs font-semibold text-slate-700">
            {a.action_type.replace(/_/g, " ")}
          </p>
          {a.note && (
            <p className="mt-0.5 text-xs text-slate-500">{a.note}</p>
          )}
          <p className="mt-0.5 text-[10px] text-slate-400">
            {new Date(a.created_at).toLocaleString("en-IN")}
          </p>
        </motion.li>
      ))}
    </motion.ol>
  );
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get<DashboardSummary>("/dashboard/summary");
        if (res.success && res.data) {
          setSummary(res.data);
        } else {
          setError("Could not load dashboard.");
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
        Loading dashboard…
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-sm text-red-700">
        {error}
      </div>
    );
  }

  return (
    <motion.div
      variants={staggerContainerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-8"
    >
      {/* Header */}
      <motion.div
        variants={fadeUpVariants}
        className="flex flex-col sm:flex-row sm:items-center justify-between gap-4"
      >
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Client Dashboard
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Track your website projects and studio updates.
          </p>
        </div>
        <motion.div {...buttonPressProps}>
          <Link
            href="/dashboard/projects/new"
            className="inline-flex items-center gap-2 rounded bg-slate-900 px-4 py-2.5 text-xs font-semibold text-white hover:bg-slate-800 transition-colors shadow-sm"
          >
            <Plus className="h-3.5 w-3.5" />
            Start New Project
          </Link>
        </motion.div>
      </motion.div>

      {/* Stats Cards */}
      <motion.div variants={fadeUpVariants} className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        <motion.div
          {...cardHoverProps}
          className="rounded-lg border border-slate-200 bg-white p-5 transition-shadow hover:shadow-sm"
        >
          <div className="flex items-center gap-2 text-slate-400 mb-2">
            <FolderOpen className="h-4 w-4" />
            <span className="text-xs font-semibold uppercase tracking-wide">Total Projects</span>
          </div>
          <p className="text-3xl font-extrabold text-slate-900">{summary?.total_projects ?? 0}</p>
        </motion.div>

        <motion.div
          {...cardHoverProps}
          className="rounded-lg border border-slate-200 bg-white p-5 transition-shadow hover:shadow-sm"
        >
          <div className="flex items-center gap-2 text-slate-400 mb-2">
            <TrendingUp className="h-4 w-4" />
            <span className="text-xs font-semibold uppercase tracking-wide">Active Project</span>
          </div>
          <p className="text-sm font-bold text-slate-900 truncate">
            {summary?.active_project?.title ?? "—"}
          </p>
          {summary?.active_project && (
            <span
              className={`mt-1 inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                STATUS_COLORS[summary.active_project.status] ?? "bg-slate-100 text-slate-500"
              }`}
            >
              {STATUS_LABELS[summary.active_project.status]}
            </span>
          )}
        </motion.div>

        <motion.div
          {...cardHoverProps}
          className="rounded-lg border border-slate-200 bg-white p-5 col-span-2 sm:col-span-1 transition-shadow hover:shadow-sm"
        >
          <div className="flex items-center gap-2 text-slate-400 mb-2">
            <Clock className="h-4 w-4" />
            <span className="text-xs font-semibold uppercase tracking-wide">Recent Activity</span>
          </div>
          <p className="text-3xl font-extrabold text-slate-900">
            {summary?.recent_activities?.length ?? 0}
          </p>
        </motion.div>
      </motion.div>

      {/* Active project quick-action */}
      {summary?.active_project && (
        <motion.div
          variants={fadeUpVariants}
          className="rounded-lg border border-blue-100 bg-blue-50 p-5 shadow-sm"
        >
          <p className="text-xs font-bold uppercase tracking-wider text-blue-600 mb-1">
            Active Project
          </p>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <p className="text-sm font-bold text-slate-900">
                {summary.active_project.title}
              </p>
              <p className="text-xs text-slate-500">{summary.active_project.business_name}</p>
            </div>
            <div className="flex gap-2">
              {summary.active_project.status === "NEW" && (
                <Link
                  href={`/dashboard/projects/${summary.active_project.id}/requirements`}
                  className="inline-flex items-center gap-1 rounded bg-slate-900 px-3 py-2 text-xs font-semibold text-white hover:bg-slate-800 transition-colors"
                >
                  Submit Requirements
                  <ArrowRight className="h-3 w-3" />
                </Link>
              )}
              <Link
                href={`/dashboard/projects/${summary.active_project.id}`}
                className="inline-flex items-center gap-1 rounded border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
              >
                View Project
              </Link>
            </div>
          </div>
        </motion.div>
      )}

      {/* Two column: recent projects + activity feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Projects */}
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-900">Recent Projects</h2>
            <Link
              href="/dashboard/projects"
              className="text-xs font-semibold text-blue-600 hover:underline"
            >
              View all
            </Link>
          </div>
          {!summary?.recent_projects?.length ? (
            <motion.div
              variants={fadeUpVariants}
              className="rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center"
            >
              <FolderOpen className="h-8 w-8 text-slate-300 mx-auto mb-3" />
              <p className="text-sm font-semibold text-slate-700">No projects yet</p>
              <p className="text-xs text-slate-500 mt-1">
                Start your first website project and our team will be in touch.
              </p>
              <Link
                href="/dashboard/projects/new"
                className="mt-4 inline-flex items-center gap-1 rounded bg-slate-900 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800 transition-colors"
              >
                <Plus className="h-3.5 w-3.5" />
                Start a Project
              </Link>
            </motion.div>
          ) : (
            <motion.div variants={staggerContainerVariants} className="space-y-3">
              {summary.recent_projects.map((p) => (
                <ProjectCard key={p.id} project={p} />
              ))}
            </motion.div>
          )}
        </div>

        {/* Activity Feed */}
        <div>
          <h2 className="text-sm font-bold text-slate-900 mb-3">Activity Timeline</h2>
          <motion.div
            variants={fadeUpVariants}
            className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
          >
            <ActivityFeed activities={summary?.recent_activities ?? []} />
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}
