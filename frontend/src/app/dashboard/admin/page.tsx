"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  Briefcase,
  CheckCircle2,
  Clock,
  Cpu,
  CreditCard,
  ExternalLink,
  Eye,
  Filter,
  Globe,
  History,
  Loader2,
  Mail,
  MessageSquare,
  Phone,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  UserCheck,
  Users,
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { api, ApiError } from "@/lib/api";
import { authStorage } from "@/lib/auth";
import {
  AdminProjectItem,
  InquiryItem,
  ProjectStatus,
  StaffUserItem,
  User,
  WebsiteBuildItem,
} from "@/types";
import { alertVariants, buttonPressProps, fadeUpVariants, staggerContainerVariants } from "@/lib/motion";

const ALL_PROJECT_STATUSES: ProjectStatus[] = [
  "NEW",
  "REQUIREMENTS_PENDING",
  "PENDING_APPROVAL",
  "BUILDING",
  "IN_PROGRESS",
  "DESIGN_REVIEW",
  "DEVELOPMENT",
  "CLIENT_REVIEW",
  "REVISION_REQUESTED",
  "APPROVED",
  "PAYMENT_PENDING",
  "DEPLOYING",
  "LIVE",
  "COMPLETED",
];

const INQUIRY_STATUSES = ["NEW", "CONTACTED", "QUALIFIED", "CONVERTED", "CLOSED"];

export default function AdminConsolePage() {
  const [user, setUser] = useState<User | null>(null);
  const [activeTab, setActiveTab] = useState<"projects" | "inquiries" | "team">("projects");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Data states
  const [overview, setOverview] = useState<any>(null);
  const [projects, setProjects] = useState<AdminProjectItem[]>([]);
  const [inquiries, setInquiries] = useState<InquiryItem[]>([]);
  const [team, setTeam] = useState<StaffUserItem[]>([]);

  // Filter states
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [inquiryStatusFilter, setInquiryStatusFilter] = useState<string>("ALL");

  // Selected project for editing / building
  const [editingProject, setEditingProject] = useState<AdminProjectItem | null>(null);
  const [modalTab, setModalTab] = useState<"settings" | "builder">("settings");
  const [editStatus, setEditStatus] = useState<ProjectStatus>("NEW");
  const [editDeveloperId, setEditDeveloperId] = useState<string>("");
  const [editPreviewUrl, setEditPreviewUrl] = useState<string>("");
  const [editProductionUrl, setEditProductionUrl] = useState<string>("");
  const [isSavingProject, setIsSavingProject] = useState(false);

  // AI Builder state
  const [projectBuilds, setProjectBuilds] = useState<WebsiteBuildItem[]>([]);
  const [loadingBuilds, setLoadingBuilds] = useState(false);
  const [buildNotes, setBuildNotes] = useState("");
  const [forceOverridePayment, setForceOverridePayment] = useState(false);
  const [isStartingBuild, setIsStartingBuild] = useState(false);

  useEffect(() => {
    const currentUser = authStorage.getUser();
    setUser(currentUser);
  }, []);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Overview metrics
      try {
        const overviewRes = await api.get<any>("/admin/overview");
        if (overviewRes.success) {
          setOverview(overviewRes.data);
        }
      } catch {
        // Non-admin developers might not access /overview
      }

      // 2. Team members
      const teamRes = await api.get<StaffUserItem[]>("/admin/team");
      if (teamRes.success && teamRes.data) {
        setTeam(teamRes.data);
      }

      // 3. Projects
      const projRes = await api.get<AdminProjectItem[]>("/admin/projects");
      if (projRes.success && projRes.data) {
        setProjects(projRes.data);
      }

      // 4. Inquiries
      const inqRes = await api.get<InquiryItem[]>("/admin/inquiries");
      if (inqRes.success && inqRes.data) {
        setInquiries(inqRes.data);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load studio operations data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user && (user.role === "ADMIN" || user.role === "DEVELOPER")) {
      loadData();
    } else if (user && user.role === "CUSTOMER") {
      setLoading(false);
    }
  }, [user, loadData]);

  const loadProjectBuilds = async (projectId: string) => {
    setLoadingBuilds(true);
    try {
      const res = await api.get<WebsiteBuildItem[]>(`/admin/projects/${projectId}/builds`);
      if (res.success && res.data) {
        setProjectBuilds(res.data);
      }
    } catch {
      setProjectBuilds([]);
    } finally {
      setLoadingBuilds(false);
    }
  };

  const handleEditClick = (p: AdminProjectItem, initialTab: "settings" | "builder" = "settings") => {
    setEditingProject(p);
    setModalTab(initialTab);
    setEditStatus(p.status);
    setEditDeveloperId(p.assigned_developer_id || "");
    setEditPreviewUrl(p.preview_url || "");
    setEditProductionUrl(p.production_url || "");
    setBuildNotes("");
    setForceOverridePayment(false);
    loadProjectBuilds(p.id);
  };

  const handleApproveAndStartBuild = async () => {
    if (!editingProject) return;

    if (forceOverridePayment) {
      const confirmed = window.confirm(
        "CONFIRM PAYMENT WAIVER:\n\nYou are approving this project without verified advance payment. Are you sure you want to grant an administrative waiver?"
      );
      if (!confirmed) return;
    }

    setIsStartingBuild(true);
    setError(null);
    setSuccess(null);

    try {
      const res = await api.post<any>(`/admin/projects/${editingProject.id}/approve-build`, {
        admin_notes: buildNotes.trim() || undefined,
        force_override_payment: forceOverridePayment,
        waive_payment: forceOverridePayment,
      });

      if (res.success) {
        const buildVer = res.data?.build?.version_number || 1;
        setSuccess(`Project approved! AI Website Build v${buildVer} queued successfully.`);
        setBuildNotes("");
        setForceOverridePayment(false);
        await loadProjectBuilds(editingProject.id);
        await loadData();
      }
    } catch (err: any) {
      setError(err?.message || "Failed to approve project and queue build.");
    } finally {
      setIsStartingBuild(false);
    }
  };

  const handleSaveProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingProject) return;

    setIsSavingProject(true);
    setError(null);
    setSuccess(null);

    try {
      const res = await api.patch<AdminProjectItem>(`/admin/projects/${editingProject.id}`, {
        status: editStatus,
        assigned_developer_id: editDeveloperId,
        preview_url: editPreviewUrl,
        production_url: editProductionUrl,
      });

      if (res.success && res.data) {
        setSuccess(`Project ${editingProject.project_number} updated successfully.`);
        setEditingProject(null);
        await loadData();
      }
    } catch (err: any) {
      setError(err?.message || "Failed to update project.");
    } finally {
      setIsSavingProject(false);
    }
  };

  const handleUpdateInquiryStatus = async (inquiryId: string, newStatus: string) => {
    try {
      const res = await api.patch<InquiryItem>(`/admin/inquiries/${inquiryId}`, {
        status: newStatus,
      });
      if (res.success) {
        setSuccess(`Lead status updated to ${newStatus}.`);
        setInquiries((prev) =>
          prev.map((i) => (i.id === inquiryId ? { ...i, status: newStatus } : i))
        );
      }
    } catch (err: any) {
      setError(err?.message || "Failed to update inquiry status.");
    }
  };

  // RBAC Access Guard
  if (user && user.role === "CUSTOMER") {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-8 text-center max-w-xl mx-auto my-12">
        <ShieldAlert className="h-10 w-10 text-red-500 mx-auto mb-3" />
        <h2 className="text-base font-bold text-red-900">Restricted Operations Console</h2>
        <p className="mt-1 text-xs text-red-700 leading-relaxed">
          Access denied. The studio operations console is strictly reserved for Studio Administrators and Lead Developers.
        </p>
        <div className="mt-4">
          <Link
            href="/dashboard"
            className="inline-flex items-center text-xs font-semibold text-red-800 underline hover:text-red-950"
          >
            &larr; Return to Customer Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const filteredProjects = projects.filter((p) => {
    const matchesStatus = statusFilter === "ALL" || p.status === statusFilter;
    const matchesSearch =
      searchQuery === "" ||
      p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.business_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.project_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (p.customer?.full_name || "").toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const filteredInquiries = inquiries.filter((i) => {
    return inquiryStatusFilter === "ALL" || i.status === inquiryStatusFilter;
  });

  return (
    <motion.div
      variants={staggerContainerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6 max-w-6xl"
    >
      {/* Header */}
      <motion.div variants={fadeUpVariants} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">Studio Operations Console</h1>
            <span className="inline-flex items-center gap-1 rounded bg-slate-900 px-2 py-0.5 text-[11px] font-bold text-white uppercase tracking-wider">
              <ShieldCheck className="h-3 w-3 text-emerald-400" />
              {user?.role || "STAFF"}
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Internal dispatch, development pipelines, lead CRM, and staff assignment center.
          </p>
        </div>

        <motion.div {...buttonPressProps}>
          <button
            type="button"
            onClick={loadData}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-sm"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh Data
          </button>
        </motion.div>
      </motion.div>

      {/* Overview Statistics Banner */}
      {overview && (
        <motion.div variants={fadeUpVariants} className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Total Projects</p>
            <p className="mt-1 text-2xl font-black text-slate-900">{overview.total_projects}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Active Builds</p>
            <p className="mt-1 text-2xl font-black text-blue-600">{overview.active_projects}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Total Leads & CRM</p>
            <p className="mt-1 text-2xl font-black text-emerald-600">{overview.total_inquiries}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">System Status</p>
            <div className="mt-1 flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                {overview.system_status}
              </span>
            </div>
          </div>
        </motion.div>
      )}

      {/* Alert Messages */}
      <AnimatePresence>
        {error && (
          <motion.div
            variants={alertVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700"
          >
            <AlertCircle className="h-4 w-4 shrink-0 text-red-500 mt-0.5" />
            <span>{error}</span>
          </motion.div>
        )}
        {success && (
          <motion.div
            variants={alertVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="flex items-start gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-800"
          >
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600 mt-0.5" />
            <span>{success}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200">
        <button
          type="button"
          onClick={() => setActiveTab("projects")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-xs font-bold transition-colors ${
            activeTab === "projects"
              ? "border-slate-900 text-slate-900"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <Briefcase className="h-4 w-4" />
          Project Pipelines ({projects.length})
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("inquiries")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-xs font-bold transition-colors ${
            activeTab === "inquiries"
              ? "border-slate-900 text-slate-900"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <Mail className="h-4 w-4" />
          Lead CRM & Inquiries ({inquiries.length})
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("team")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-xs font-bold transition-colors ${
            activeTab === "team"
              ? "border-slate-900 text-slate-900"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <Users className="h-4 w-4" />
          Studio Team ({team.length})
        </button>
      </div>

      {/* TAB 1: PROJECTS PIPELINE */}
      {activeTab === "projects" && (
        <div className="space-y-4">
          {/* Filters Bar */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white p-3 rounded-lg border border-slate-200">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search title, client, or PRJ number..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-md border border-slate-300 pl-8 pr-3 py-1.5 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-slate-900"
              />
            </div>

            <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
              <Filter className="h-3.5 w-3.5 text-slate-400 shrink-0" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 focus:outline-none focus:border-slate-900"
              >
                <option value="ALL">All Statuses ({projects.length})</option>
                {ALL_PROJECT_STATUSES.map((st) => (
                  <option key={st} value={st}>
                    {st.replace(/_/g, " ")}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Projects Table / Cards */}
          {loading ? (
            <div className="flex items-center justify-center py-16 text-slate-400 text-xs">
              <Loader2 className="h-5 w-5 animate-spin mr-2" />
              Loading studio pipelines…
            </div>
          ) : filteredProjects.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-200 p-12 text-center text-xs text-slate-400">
              No projects found matching the selected criteria.
            </div>
          ) : (
            <div className="space-y-3">
              {filteredProjects.map((p) => (
                <div
                  key={p.id}
                  className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm hover:border-slate-300 transition-all"
                >
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 pb-3 border-b border-slate-100">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">
                          {p.project_number}
                        </span>
                        <h3 className="text-sm font-bold text-slate-900">{p.title}</h3>
                        <span className="text-xs text-slate-400">({p.business_name})</span>
                      </div>
                      <p className="mt-1 text-xs text-slate-500">
                        Client: <span className="font-semibold text-slate-700">{p.customer?.full_name || "N/A"}</span> &bull; {p.customer?.phone || ""} {p.customer?.email ? `(${p.customer.email})` : ""}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-semibold text-slate-800 border border-slate-200">
                        {p.status.replace(/_/g, " ")}
                      </span>
                      <motion.div {...buttonPressProps}>
                        <button
                          type="button"
                          onClick={() => handleEditClick(p, "builder")}
                          className="inline-flex items-center gap-1 rounded-md bg-violet-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-violet-700 transition-colors shadow-sm"
                        >
                          <Sparkles className="h-3 w-3" />
                          AI Builder
                        </button>
                      </motion.div>
                      <motion.div {...buttonPressProps}>
                        <button
                          type="button"
                          onClick={() => handleEditClick(p, "settings")}
                          className="rounded-md bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-800 transition-colors shadow-sm"
                        >
                          Settings
                        </button>
                      </motion.div>
                    </div>
                  </div>

                  <div className="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                    <div>
                      <span className="text-[10px] font-bold uppercase text-slate-400 block">Package Tier</span>
                      <span className="font-medium text-slate-800">{p.package_name || "Custom Tier"}</span>
                    </div>
                    <div>
                      <span className="text-[10px] font-bold uppercase text-slate-400 block">Assigned Developer</span>
                      <span className="font-medium text-slate-800">
                        {p.assigned_developer ? (
                          <span className="inline-flex items-center gap-1 text-emerald-700">
                            <UserCheck className="h-3 w-3" />
                            {p.assigned_developer.full_name}
                          </span>
                        ) : (
                          <span className="text-amber-600 font-semibold">Unassigned</span>
                        )}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] font-bold uppercase text-slate-400 block">Staging Preview</span>
                      {p.preview_url ? (
                        <a
                          href={p.preview_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-blue-600 hover:underline truncate max-w-[200px]"
                        >
                          <ExternalLink className="h-3 w-3" />
                          View Staging
                        </a>
                      ) : (
                        <span className="text-slate-400 italic">No preview URL configured</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Edit Project & AI Builder Modal */}
          <AnimatePresence>
            {editingProject && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-xs">
                <motion.div
                  variants={fadeUpVariants}
                  initial="hidden"
                  animate="visible"
                  exit="hidden"
                  className="w-full max-w-xl rounded-xl border border-slate-200 bg-white p-6 shadow-xl max-h-[90vh] overflow-y-auto"
                >
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-bold text-slate-900">
                          {editingProject.project_number}: {editingProject.title}
                        </h3>
                        <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-700 uppercase">
                          {editingProject.status.replace(/_/g, " ")}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500">Client: {editingProject.customer?.full_name || "N/A"}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setEditingProject(null)}
                      className="text-xs text-slate-400 hover:text-slate-600 font-medium"
                    >
                      Close
                    </button>
                  </div>

                  {/* Modal Subtabs */}
                  <div className="mt-3 flex gap-2 border-b border-slate-100 pb-2">
                    <button
                      type="button"
                      onClick={() => setModalTab("builder")}
                      className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-bold transition-colors ${
                        modalTab === "builder"
                          ? "bg-violet-50 text-violet-700 border border-violet-200"
                          : "text-slate-500 hover:bg-slate-50"
                      }`}
                    >
                      <Sparkles className="h-3.5 w-3.5" />
                      AI Website Builder
                    </button>
                    <button
                      type="button"
                      onClick={() => setModalTab("settings")}
                      className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-bold transition-colors ${
                        modalTab === "settings"
                          ? "bg-slate-100 text-slate-900 border border-slate-200"
                          : "text-slate-500 hover:bg-slate-50"
                      }`}
                    >
                      <Briefcase className="h-3.5 w-3.5" />
                      Project Settings
                    </button>
                  </div>

                  {/* TAB 1: AI WEBSITE BUILDER DISPATCH */}
                  {modalTab === "builder" && (
                    <div className="mt-4 space-y-4 text-xs">
                      <div className="rounded-lg border border-violet-100 bg-violet-50/60 p-3.5">
                        <div className="flex items-center gap-1.5 text-violet-900 font-bold">
                          <Cpu className="h-4 w-4 text-violet-600" />
                          <span>Internal AI Generation Engine</span>
                        </div>
                        <p className="mt-1 text-[11px] text-violet-700 leading-relaxed">
                          Verify client requirements, uploaded brand assets, and advance payment status before triggering
                          the internal AI Website Builder. All builds are versioned and require admin authorization.
                        </p>
                      </div>

                      {/* Build History */}
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-bold text-slate-700 flex items-center gap-1">
                            <History className="h-3.5 w-3.5 text-slate-400" />
                            Build Run Versions ({projectBuilds.length})
                          </span>
                          <button
                            type="button"
                            onClick={() => loadProjectBuilds(editingProject.id)}
                            disabled={loadingBuilds}
                            className="text-[11px] text-blue-600 hover:underline"
                          >
                            {loadingBuilds ? "Refreshing…" : "Refresh"}
                          </button>
                        </div>

                        {loadingBuilds ? (
                          <div className="py-4 text-center text-slate-400">Loading build history…</div>
                        ) : projectBuilds.length === 0 ? (
                          <div className="rounded-lg border border-dashed border-slate-200 p-4 text-center text-slate-400">
                            No AI website builds have been initiated for this project yet.
                          </div>
                        ) : (
                          <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                            {projectBuilds.map((b) => (
                              <div
                                key={b.id}
                                className={`rounded-lg border p-2.5 flex items-center justify-between ${
                                  b.is_active ? "border-violet-300 bg-violet-50/30" : "border-slate-200 bg-slate-50/40"
                                }`}
                              >
                                <div>
                                  <div className="flex items-center gap-2">
                                    <span className="font-mono font-bold text-slate-900">v{b.version_number}</span>
                                    <span
                                      className={`rounded px-1.5 py-0.2 text-[10px] font-bold uppercase ${
                                        b.status === "COMPLETED"
                                          ? "bg-emerald-100 text-emerald-800"
                                          : b.status === "FAILED"
                                          ? "bg-red-100 text-red-800"
                                          : "bg-blue-100 text-blue-800"
                                      }`}
                                    >
                                      {b.status}
                                    </span>
                                    {b.is_active && (
                                      <span className="rounded bg-violet-100 text-violet-700 px-1 py-0.2 text-[9px] font-bold uppercase">
                                        Active
                                      </span>
                                    )}
                                  </div>
                                  {b.admin_notes && (
                                    <p className="mt-0.5 text-[11px] text-slate-600 italic truncate max-w-xs">
                                      &ldquo;{b.admin_notes}&rdquo;
                                    </p>
                                  )}
                                </div>
                                <div className="flex items-center gap-2">
                                  {b.review_status && (
                                    <span
                                      className={`rounded border px-1.5 py-0.2 text-[9px] font-bold uppercase ${
                                        b.review_status === "APPROVED"
                                          ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                                          : b.review_status === "REJECTED"
                                          ? "border-red-200 bg-red-50 text-red-700"
                                          : "border-amber-200 bg-amber-50 text-amber-700"
                                      }`}
                                    >
                                      {b.review_status.replace(/_/g, " ")}
                                    </span>
                                  )}
                                  <Link
                                    href={`/dashboard/admin/projects/${editingProject.id}/builds/${b.id}`}
                                    className="inline-flex items-center gap-1 rounded bg-slate-900 px-2 py-1 text-[10px] font-semibold text-white hover:bg-slate-800 transition-colors"
                                  >
                                    <Eye className="h-3 w-3" /> Review
                                  </Link>
                                  <span className="text-[10px] text-slate-400">
                                    {new Date(b.created_at).toLocaleDateString("en-IN")}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Approval & Build Trigger */}
                      <div className="rounded-lg border border-slate-200 bg-slate-50/50 p-4 space-y-3">
                        <span className="font-bold text-slate-900 block">Approve & Start New Build Run</span>

                        {/* Payment Verification Status Badge */}
                        <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-3">
                          <div className="flex items-center gap-2">
                            <CreditCard className="h-4 w-4 text-slate-500" />
                            <span className="font-semibold text-slate-700">Advance Payment:</span>
                          </div>
                          {editingProject.advance_payment_status === "PAID" ? (
                            <span className="inline-flex items-center gap-1 rounded bg-emerald-100 px-2 py-0.5 text-[11px] font-bold text-emerald-800">
                              <CheckCircle2 className="h-3 w-3" />
                              Paid (₹{(editingProject.total_paid_inr || 0).toLocaleString("en-IN")})
                            </span>
                          ) : forceOverridePayment ? (
                            <span className="inline-flex items-center gap-1 rounded bg-purple-100 px-2 py-0.5 text-[11px] font-bold text-purple-800">
                              <AlertCircle className="h-3 w-3" />
                              Payment Waived
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 rounded bg-amber-100 px-2 py-0.5 text-[11px] font-bold text-amber-800">
                              <Clock className="h-3 w-3" />
                              Pending
                            </span>
                          )}
                        </div>

                        <div>
                          <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                            Admin Build Directives / Instructions (Optional)
                          </label>
                          <textarea
                            rows={2}
                            value={buildNotes}
                            onChange={(e) => setBuildNotes(e.target.value)}
                            placeholder="e.g., Focus on dark luxury aesthetics, prioritize hero section with booking CTA..."
                            className="w-full rounded-md border border-slate-300 p-2 text-slate-900 focus:outline-none focus:border-slate-900"
                          />
                        </div>

                        {/* Waive Advance Payment Control */}
                        <div className="rounded-lg border border-slate-200 bg-white p-3 space-y-2">
                          <div className="flex items-start gap-2">
                            <input
                              type="checkbox"
                              id="waivePaymentControl"
                              checked={forceOverridePayment}
                              onChange={(e) => setForceOverridePayment(e.target.checked)}
                              className="h-4 w-4 mt-0.5 rounded border-slate-300 text-slate-900 focus:ring-slate-900 cursor-pointer"
                            />
                            <div>
                              <label htmlFor="waivePaymentControl" className="font-bold text-slate-800 cursor-pointer block">
                                Waive Advance Payment
                              </label>
                              <p className="text-[11px] text-slate-500 mt-0.5">
                                Allow build approval without requiring verified advance payment. Only use for authorized clients, internal development, or approved offline billing.
                              </p>
                            </div>
                          </div>

                          {forceOverridePayment && (
                            <div className="rounded border border-amber-200 bg-amber-50 p-2.5 text-[11px] text-amber-800 flex items-start gap-1.5">
                              <AlertCircle className="h-3.5 w-3.5 text-amber-600 shrink-0 mt-0.5" />
                              <span>
                                <strong>Administrative Waiver Active:</strong> Advance payment check will be bypassed. An explicit confirmation dialog will appear before queuing the build.
                              </span>
                            </div>
                          )}
                        </div>

                        <motion.button
                          {...buttonPressProps}
                          type="button"
                          onClick={handleApproveAndStartBuild}
                          disabled={isStartingBuild}
                          className="w-full inline-flex items-center justify-center gap-1.5 rounded-md bg-violet-600 px-4 py-2.5 text-xs font-semibold text-white hover:bg-violet-700 transition-colors shadow-sm disabled:opacity-50"
                        >
                          {isStartingBuild ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <Sparkles className="h-3.5 w-3.5" />
                          )}
                          Approve Request & Queue AI Build (v{(projectBuilds[0]?.version_number || 0) + 1})
                        </motion.button>
                      </div>
                    </div>
                  )}

                  {/* TAB 2: PROJECT SETTINGS */}
                  {modalTab === "settings" && (
                    <form onSubmit={handleSaveProject} className="mt-4 space-y-4 text-xs">
                      <div>
                        <label className="block font-semibold text-slate-700 mb-1">Lifecycle Status</label>
                        <select
                          value={editStatus}
                          onChange={(e) => setEditStatus(e.target.value as ProjectStatus)}
                          className="w-full rounded-md border border-slate-300 bg-white p-2 font-medium text-slate-900 focus:outline-none focus:border-slate-900"
                        >
                          {ALL_PROJECT_STATUSES.map((st) => (
                            <option key={st} value={st}>
                              {st.replace(/_/g, " ")}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="block font-semibold text-slate-700 mb-1">Assign Lead Developer</label>
                        <select
                          value={editDeveloperId}
                          onChange={(e) => setEditDeveloperId(e.target.value)}
                          className="w-full rounded-md border border-slate-300 bg-white p-2 font-medium text-slate-900 focus:outline-none focus:border-slate-900"
                        >
                          <option value="">-- Unassigned --</option>
                          {team.map((m) => (
                            <option key={m.id} value={m.id}>
                              {m.full_name} ({m.role})
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="block font-semibold text-slate-700 mb-1">Staging Preview URL</label>
                        <input
                          type="url"
                          placeholder="https://staging.preview.nexusstudio.dev"
                          value={editPreviewUrl}
                          onChange={(e) => setEditPreviewUrl(e.target.value)}
                          className="w-full rounded-md border border-slate-300 p-2 text-slate-900 focus:outline-none focus:border-slate-900"
                        />
                      </div>

                      <div>
                        <label className="block font-semibold text-slate-700 mb-1">Live Production URL</label>
                        <input
                          type="url"
                          placeholder="https://client-domain.com"
                          value={editProductionUrl}
                          onChange={(e) => setEditProductionUrl(e.target.value)}
                          className="w-full rounded-md border border-slate-300 p-2 text-slate-900 focus:outline-none focus:border-slate-900"
                        />
                      </div>

                      <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                        <button
                          type="button"
                          onClick={() => setEditingProject(null)}
                          className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
                        >
                          Cancel
                        </button>
                        <motion.button
                          {...buttonPressProps}
                          type="submit"
                          disabled={isSavingProject}
                          className="inline-flex items-center gap-1.5 rounded-md bg-slate-900 px-4 py-1.5 text-xs font-semibold text-white hover:bg-slate-800 transition-colors disabled:opacity-50"
                        >
                          {isSavingProject && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                          Save Changes
                        </motion.button>
                      </div>
                    </form>
                  )}
                </motion.div>
              </div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* TAB 2: LEAD CRM & INQUIRIES */}
      {activeTab === "inquiries" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between bg-white p-3 rounded-lg border border-slate-200">
            <span className="text-xs font-bold text-slate-700">Filter Inquiries by Status:</span>
            <select
              value={inquiryStatusFilter}
              onChange={(e) => setInquiryStatusFilter(e.target.value)}
              className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 focus:outline-none focus:border-slate-900"
            >
              <option value="ALL">All Leads ({inquiries.length})</option>
              {INQUIRY_STATUSES.map((st) => (
                <option key={st} value={st}>
                  {st}
                </option>
              ))}
            </select>
          </div>

          {filteredInquiries.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-200 p-12 text-center text-xs text-slate-400">
              No leads found matching status filter.
            </div>
          ) : (
            <div className="space-y-3">
              {filteredInquiries.map((inq) => (
                <div
                  key={inq.id}
                  className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm hover:border-slate-300 transition-all text-xs"
                >
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 pb-3 border-b border-slate-100">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-bold text-slate-900 text-sm">{inq.name}</h3>
                        {inq.business_name && (
                          <span className="text-slate-500 font-medium">({inq.business_name})</span>
                        )}
                        <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-600 uppercase">
                          {inq.source}
                        </span>
                      </div>
                      <div className="mt-1 flex flex-wrap items-center gap-3 text-slate-500">
                        {inq.phone && (
                          <span className="flex items-center gap-1">
                            <Phone className="h-3 w-3 text-slate-400" />
                            <a href={`tel:${inq.phone}`} className="hover:text-blue-600 transition-colors">
                              {inq.phone}
                            </a>
                          </span>
                        )}
                        {inq.email && (
                          <span className="flex items-center gap-1">
                            <Mail className="h-3 w-3 text-slate-400" />
                            <a href={`mailto:${inq.email}`} className="hover:text-blue-600 transition-colors">
                              {inq.email}
                            </a>
                          </span>
                        )}
                        {inq.city && <span>&bull; {inq.city}</span>}
                      </div>
                      {inq.subject && (
                        <div className="mt-1.5 text-xs text-slate-700">
                          <span className="font-semibold text-slate-800">Subject:</span> {inq.subject}
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="font-bold uppercase text-[10px] text-slate-400">Status:</span>
                      <select
                        value={inq.status}
                        onChange={(e) => handleUpdateInquiryStatus(inq.id, e.target.value)}
                        className="rounded border border-slate-300 bg-white px-2 py-1 text-xs font-semibold text-slate-800 focus:outline-none focus:border-slate-900"
                      >
                        {INQUIRY_STATUSES.map((st) => (
                          <option key={st} value={st}>
                            {st}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {inq.message && (
                    <div className="mt-3 rounded-lg bg-slate-50 p-3 text-slate-700 leading-relaxed font-normal">
                      &ldquo;{inq.message}&rdquo;
                    </div>
                  )}

                  <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-400">
                    <span>Package of interest: {inq.selected_package || "General Inquiry"}</span>
                    <span>Received: {new Date(inq.created_at).toLocaleString("en-IN")}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: STUDIO TEAM */}
      {activeTab === "team" && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4">Studio Team Directory</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {team.map((m) => (
              <div key={m.id} className="rounded-lg border border-slate-200 p-4 bg-slate-50/50">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-slate-900 text-xs">{m.full_name}</h4>
                  <span
                    className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase ${
                      m.role === "ADMIN" ? "bg-purple-100 text-purple-800" : "bg-blue-100 text-blue-800"
                    }`}
                  >
                    {m.role}
                  </span>
                </div>
                <p className="mt-1 text-xs text-slate-500">{m.email}</p>
                {m.phone && <p className="text-[11px] text-slate-400 mt-0.5">{m.phone}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}
