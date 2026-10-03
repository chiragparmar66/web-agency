"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle2,
  Lock,
  Save,
  Send,
  AlertCircle,
  Plus,
  Trash2,
  Clock,
  Sparkles,
} from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { RequirementItem, ProjectDetail } from "@/types";
import { motion, AnimatePresence } from "motion/react";
import { fadeUpVariants, alertVariants, buttonPressProps } from "@/lib/motion";

export default function RequirementsPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params?.id as string;

  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [requirements, setRequirements] = useState<RequirementItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [lastSaved, setLastSaved] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Form state
  const [businessSummary, setBusinessSummary] = useState("");
  const [targetAudience, setTargetAudience] = useState("");
  const [servicesOffered, setServicesOffered] = useState("");
  const [colorPreferences, setColorPreferences] = useState("");
  const [referenceWebsites, setReferenceWebsites] = useState<string[]>([""]);
  const [contactEmail, setContactEmail] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [physicalAddress, setPhysicalAddress] = useState("");
  const [socialInstagram, setSocialInstagram] = useState("");
  const [socialLinkedin, setSocialLinkedin] = useState("");
  const [socialTwitter, setSocialTwitter] = useState("");
  const [socialFacebook, setSocialFacebook] = useState("");
  const [specialRequests, setSpecialRequests] = useState("");

  const isLocked = Boolean(requirements?.is_submitted);

  // Load project and requirements
  useEffect(() => {
    if (!projectId) return;

    const loadData = async () => {
      try {
        const [projRes, reqRes] = await Promise.all([
          api.get<ProjectDetail>(`/projects/${projectId}`),
          api.get<RequirementItem>(`/projects/${projectId}/requirements`),
        ]);

        if (projRes.success && projRes.data) {
          setProject(projRes.data);
        }

        if (reqRes.success && reqRes.data) {
          const req = reqRes.data;
          setRequirements(req);
          setBusinessSummary(req.business_summary || "");
          setTargetAudience(req.target_audience || "");
          setServicesOffered(req.services_offered || "");
          setColorPreferences(req.color_preferences || "");
          setReferenceWebsites(
            req.reference_websites && req.reference_websites.length > 0
              ? req.reference_websites
              : [""]
          );
          setContactEmail(req.contact_email || "");
          setContactPhone(req.contact_phone || "");
          setPhysicalAddress(req.physical_address || "");
          setSpecialRequests(req.special_requests || "");

          const socials = req.social_links || {};
          setSocialInstagram(socials.instagram || "");
          setSocialLinkedin(socials.linkedin || "");
          setSocialTwitter(socials.twitter || "");
          setSocialFacebook(socials.facebook || "");

          if (req.updated_at) {
            setLastSaved(new Date(req.updated_at).toLocaleTimeString("en-IN"));
          }
        }
      } catch (err) {
        setErrorMessage("Could not load project specifications.");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [projectId]);

  const buildPayload = useCallback(() => {
    const cleanedReferences = referenceWebsites
      .map((url) => url.trim())
      .filter(Boolean);

    const socialLinks: Record<string, string> = {};
    if (socialInstagram.trim()) socialLinks.instagram = socialInstagram.trim();
    if (socialLinkedin.trim()) socialLinks.linkedin = socialLinkedin.trim();
    if (socialTwitter.trim()) socialLinks.twitter = socialTwitter.trim();
    if (socialFacebook.trim()) socialLinks.facebook = socialFacebook.trim();

    return {
      business_summary: businessSummary.trim() || undefined,
      target_audience: targetAudience.trim() || undefined,
      services_offered: servicesOffered.trim() || undefined,
      color_preferences: colorPreferences.trim() || undefined,
      reference_websites: cleanedReferences,
      social_links: socialLinks,
      contact_email: contactEmail.trim() || undefined,
      contact_phone: contactPhone.trim() || undefined,
      physical_address: physicalAddress.trim() || undefined,
      special_requests: specialRequests.trim() || undefined,
    };
  }, [
    businessSummary,
    targetAudience,
    servicesOffered,
    colorPreferences,
    referenceWebsites,
    contactEmail,
    contactPhone,
    physicalAddress,
    socialInstagram,
    socialLinkedin,
    socialTwitter,
    socialFacebook,
    specialRequests,
  ]);

  const handleSaveDraft = async () => {
    if (isLocked) return;
    setSaving(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const payload = buildPayload();
      const res = await api.put<RequirementItem>(
        `/projects/${projectId}/requirements`,
        payload
      );
      if (res.success && res.data) {
        setRequirements(res.data);
        setLastSaved(new Date().toLocaleTimeString("en-IN"));
        setSuccessMessage("Draft saved successfully.");
        setTimeout(() => setSuccessMessage(null), 4000);
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Failed to save draft.");
      }
    } finally {
      setSaving(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isLocked) return;

    if (!businessSummary.trim()) {
      setErrorMessage("Please provide a summary of your business.");
      return;
    }

    if (!window.confirm("Once submitted, requirements are locked for development review. Are you sure you want to finalize?")) {
      return;
    }

    setSubmitting(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const payload = buildPayload();
      const res = await api.post<RequirementItem>(
        `/projects/${projectId}/requirements/submit`,
        payload
      );
      if (res.success && res.data) {
        setRequirements(res.data);
        setSuccessMessage("Specifications finalized and locked! Please proceed with the advance payment on your project dashboard.");
        setTimeout(() => {
          router.push(`/dashboard/projects/${projectId}`);
        }, 1200);
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Failed to submit requirements.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const addReferenceWebsite = () => {
    if (isLocked) return;
    setReferenceWebsites((prev) => [...prev, ""]);
  };

  const updateReferenceWebsite = (index: number, value: string) => {
    if (isLocked) return;
    setReferenceWebsites((prev) => {
      const updated = [...prev];
      updated[index] = value;
      return updated;
    });
  };

  const removeReferenceWebsite = (index: number) => {
    if (isLocked) return;
    setReferenceWebsites((prev) => prev.filter((_, i) => i !== index));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-slate-400 text-xs">
        <div className="h-5 w-5 border-2 border-slate-300 border-t-slate-700 rounded-full animate-spin mr-2" />
        Loading project requirements…
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Navigation */}
      <Link
        href={`/dashboard/projects/${projectId}`}
        className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 font-semibold transition-colors"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to {project?.title || "Project Overview"}
      </Link>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              Project Specification
            </h1>
            {isLocked ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-slate-900 px-2.5 py-0.5 text-[11px] font-semibold text-white">
                <Lock className="h-3 w-3" />
                Submitted & Locked
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-0.5 text-[11px] font-semibold text-amber-800">
                <Clock className="h-3 w-3" />
                Draft In Progress
              </span>
            )}
          </div>
          <p className="mt-1 text-xs text-slate-500">
            {project?.title} ({project?.project_number}) &mdash; {project?.business_name}
          </p>
        </div>

        {!isLocked && (
          <div className="flex items-center gap-3">
            {lastSaved && (
              <span className="text-[11px] text-slate-400">
                Saved at {lastSaved}
              </span>
            )}
            <button
              type="button"
              onClick={handleSaveDraft}
              disabled={saving}
              className="inline-flex items-center gap-1.5 rounded border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50 transition-colors shadow-sm"
            >
              <Save className="h-3.5 w-3.5" />
              {saving ? "Saving…" : "Save Draft"}
            </button>
          </div>
        )}
      </div>

      {/* Lock banner if submitted */}
      {isLocked && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-xs text-emerald-800 flex items-start gap-3">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600 mt-0.5" />
          <div>
            <p className="font-bold">Requirements Locked for Review</p>
            <p className="mt-0.5 text-emerald-700">
              Submitted on{" "}
              {requirements?.submitted_at
                ? new Date(requirements.submitted_at).toLocaleDateString("en-IN", {
                    day: "numeric",
                    month: "short",
                    year: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })
                : "Record verified"}
              . Our engineers are using these specifications to build your website.
            </p>
          </div>
        </div>
      )}

      {/* Alerts with AnimatePresence */}
      <AnimatePresence>
        {errorMessage && (
          <motion.div
            variants={alertVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="rounded-lg border border-red-200 bg-red-50 p-4 text-xs text-red-700 flex items-center gap-2 shadow-sm"
          >
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{errorMessage}</span>
          </motion.div>
        )}

        {successMessage && (
          <motion.div
            variants={alertVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-xs text-emerald-700 flex items-center gap-2 shadow-sm"
          >
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>{successMessage}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Form Content */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Section 1: Business Overview */}
        <div className="rounded-lg border border-slate-200 bg-white p-6 space-y-4">
          <div className="border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-slate-900">1. Business Profile & Purpose</h2>
            <p className="text-xs text-slate-500">
              Help our designers and developers understand your company positioning and audience.
            </p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Business Summary & Core Mission *
            </label>
            <textarea
              rows={4}
              disabled={isLocked}
              value={businessSummary}
              onChange={(e) => setBusinessSummary(e.target.value)}
              placeholder="Describe what your business does, your unique proposition, and the primary goal of this website..."
              className="w-full rounded border border-slate-300 px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-slate-800 focus:outline-none disabled:bg-slate-50 disabled:text-slate-500"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Target Audience
              </label>
              <textarea
                rows={3}
                disabled={isLocked}
                value={targetAudience}
                onChange={(e) => setTargetAudience(e.target.value)}
                placeholder="e.g. B2B corporate managers, direct local consumers, healthcare seekers..."
                className="w-full rounded border border-slate-300 px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-slate-800 focus:outline-none disabled:bg-slate-50 disabled:text-slate-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Core Services / Products Offered
              </label>
              <textarea
                rows={3}
                disabled={isLocked}
                value={servicesOffered}
                onChange={(e) => setServicesOffered(e.target.value)}
                placeholder="List key services, product categories, or solutions to showcase on the site..."
                className="w-full rounded border border-slate-300 px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-slate-800 focus:outline-none disabled:bg-slate-50 disabled:text-slate-500"
              />
            </div>
          </div>
        </div>

        {/* Section 2: Visual & Brand Aesthetic */}
        <div className="rounded-lg border border-slate-200 bg-white p-6 space-y-4">
          <div className="border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-slate-900">2. Visual Identity & Inspiration</h2>
            <p className="text-xs text-slate-500">
              Guide the visual direction, color palettes, and reference sites you admire.
            </p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Color Preferences & Brand Theme
            </label>
            <input
              type="text"
              disabled={isLocked}
              value={colorPreferences}
              onChange={(e) => setColorPreferences(e.target.value)}
              placeholder="e.g. Navy Blue and Minimal White with gold accents; or Modern Dark Mode"
              className="w-full rounded border border-slate-300 px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-slate-800 focus:outline-none disabled:bg-slate-50 disabled:text-slate-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Reference Websites (Inspirations)
            </label>
            <p className="text-[11px] text-slate-400 mb-2">
              Share links to competitor or inspirational websites whose style, layout, or feel you appreciate.
            </p>
            <div className="space-y-2">
              {referenceWebsites.map((ref, index) => (
                <div key={index} className="flex items-center gap-2">
                  <input
                    type="url"
                    disabled={isLocked}
                    value={ref}
                    onChange={(e) => updateReferenceWebsite(index, e.target.value)}
                    placeholder="https://example.com"
                    className="flex-1 rounded border border-slate-300 px-3 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:border-slate-800 focus:outline-none disabled:bg-slate-50 disabled:text-slate-500"
                  />
                  {!isLocked && referenceWebsites.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeReferenceWebsite(index)}
                      className="p-1.5 text-slate-400 hover:text-red-600 rounded transition-colors"
                      title="Remove URL"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>

            {!isLocked && (
              <button
                type="button"
                onClick={addReferenceWebsite}
                className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:underline"
              >
                <Plus className="h-3.5 w-3.5" />
                Add another reference URL
              </button>
            )}
          </div>
        </div>

        {/* Section 3: Contact & Business Details to Display */}
        <div className="rounded-lg border border-slate-200 bg-white p-6 space-y-4">
          <div className="border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-slate-900">3. Public Contact & Social Information</h2>
            <p className="text-xs text-slate-500">
              The exact contact points that should be displayed across the website footer, header, and contact form.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Official Contact Email
              </label>
              <input
                type="email"
                disabled={isLocked}
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
                placeholder="contact@yourbusiness.com"
                className="w-full rounded border border-slate-300 px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-slate-800 focus:outline-none disabled:bg-slate-50 disabled:text-slate-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Official Phone / WhatsApp Number
              </label>
              <input
                type="tel"
                disabled={isLocked}
                value={contactPhone}
                onChange={(e) => setContactPhone(e.target.value)}
                placeholder="+91 98765 43210"
                className="w-full rounded border border-slate-300 px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-slate-800 focus:outline-none disabled:bg-slate-50 disabled:text-slate-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Physical Address / Operating City
            </label>
            <input
              type="text"
              disabled={isLocked}
              value={physicalAddress}
              onChange={(e) => setPhysicalAddress(e.target.value)}
              placeholder="e.g. Ground Floor, Sector 18, Noida, Uttar Pradesh"
              className="w-full rounded border border-slate-300 px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-slate-800 focus:outline-none disabled:bg-slate-50 disabled:text-slate-500"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Instagram URL
              </label>
              <input
                type="url"
                disabled={isLocked}
                value={socialInstagram}
                onChange={(e) => setSocialInstagram(e.target.value)}
                placeholder="https://instagram.com/yourhandle"
                className="w-full rounded border border-slate-300 px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-slate-800 focus:outline-none disabled:bg-slate-50 disabled:text-slate-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                LinkedIn URL
              </label>
              <input
                type="url"
                disabled={isLocked}
                value={socialLinkedin}
                onChange={(e) => setSocialLinkedin(e.target.value)}
                placeholder="https://linkedin.com/company/yourhandle"
                className="w-full rounded border border-slate-300 px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-slate-800 focus:outline-none disabled:bg-slate-50 disabled:text-slate-500"
              />
            </div>
          </div>
        </div>

        {/* Section 4: Special Instructions */}
        <div className="rounded-lg border border-slate-200 bg-white p-6 space-y-4">
          <div className="border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-slate-900">4. Special Requirements & Specific Notes</h2>
            <p className="text-xs text-slate-500">
              Any unique integrations, booking calendars, custom sections, or notes for the engineering team.
            </p>
          </div>

          <div>
            <textarea
              rows={4}
              disabled={isLocked}
              value={specialRequests}
              onChange={(e) => setSpecialRequests(e.target.value)}
              placeholder="e.g. Need WhatsApp floating button, multi-language support (Hindi/English), integration with Calendly, custom testimonial carousel..."
              className="w-full rounded border border-slate-300 px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-slate-800 focus:outline-none disabled:bg-slate-50 disabled:text-slate-500"
            />
          </div>
        </div>

        {/* Action Controls */}
        {!isLocked && (
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
            <motion.div {...buttonPressProps} className="w-full sm:w-auto">
              <button
                type="button"
                onClick={handleSaveDraft}
                disabled={saving || submitting}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded border border-slate-300 bg-white px-5 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50 transition-colors shadow-sm"
              >
                <Save className="h-4 w-4" />
                {saving ? "Saving Draft…" : "Save as Draft"}
              </button>
            </motion.div>

            <motion.div {...buttonPressProps} className="w-full sm:w-auto">
              <button
                type="submit"
                disabled={submitting || saving}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded bg-slate-900 px-6 py-2.5 text-xs font-semibold text-white hover:bg-slate-800 disabled:opacity-50 transition-colors shadow-sm"
              >
                {submitting ? (
                  <>
                    <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Submitting…
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4" />
                    Submit & Finalize Requirements
                  </>
                )}
              </button>
            </motion.div>
          </div>
        )}
      </form>
    </div>
  );
}
