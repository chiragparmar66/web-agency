"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ArrowRight, CheckCircle2, Loader2, AlertCircle, RefreshCw } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { api, ApiError } from "@/lib/api";
import { PricingPackage, ProjectItem } from "@/types";
import { fadeUpVariants, alertVariants } from "@/lib/motion";

export default function NewProjectPage() {
  const router = useRouter();
  const [step, setStep] = useState<1 | 2>(1);

  // Dynamic packages from backend
  const [packages, setPackages] = useState<PricingPackage[]>([]);
  const [loadingPackages, setLoadingPackages] = useState(true);
  const [packagesError, setPackagesError] = useState<string | null>(null);
  const [selectedPackageId, setSelectedPackageId] = useState<string>("");

  const [title, setTitle] = useState("");
  const [businessName, setBusinessName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPackages = useCallback(async () => {
    setLoadingPackages(true);
    setPackagesError(null);
    try {
      const res = await api.get<PricingPackage[]>("/packages");
      if (res.success && res.data && res.data.length > 0) {
        setPackages(res.data);
        const popular = res.data.find((p) => p.is_popular);
        setSelectedPackageId(popular ? popular.id : res.data[0].id);
      } else {
        setPackagesError("No active packages available. Please contact our support.");
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setPackagesError(err.message);
      } else {
        setPackagesError("Could not load pricing packages. Please check your connection.");
      }
    } finally {
      setLoadingPackages(false);
    }
  }, []);

  useEffect(() => {
    fetchPackages();
  }, [fetchPackages]);

  const selectedPackage = packages.find((p) => p.id === selectedPackageId);

  const handleSubmit = async () => {
    if (!title.trim() || !businessName.trim()) {
      setError("Please enter both a project title and business name.");
      return;
    }

    if (!selectedPackageId) {
      setError("Please select a package for your project.");
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const res = await api.post<ProjectItem>("/projects", {
        title: title.trim(),
        business_name: businessName.trim(),
        package_id: selectedPackageId,
      });
      if (res.success && res.data) {
        router.push(`/dashboard/projects/${res.data.id}`);
      } else {
        setError("Could not create project. Please try again.");
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Back */}
      <Link
        href="/dashboard/projects"
        className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 font-semibold transition-colors"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to Projects
      </Link>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
          Start a New Project
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Select an active package and tell us about your business. Our team will review your specifications.
        </p>
      </div>

      {/* Steps */}
      <div className="flex items-center gap-2 text-xs font-semibold">
        <span className={step === 1 ? "text-slate-900" : "text-slate-400"}>
          1. Choose Package
        </span>
        <ArrowRight className="h-3 w-3 text-slate-300" />
        <span className={step === 2 ? "text-slate-900" : "text-slate-400"}>
          2. Project Details
        </span>
      </div>

      <AnimatePresence mode="wait">
        {/* Step 1: Package Selection */}
        {step === 1 && (
          <motion.div
            key="step-1"
            variants={fadeUpVariants}
            initial="hidden"
            animate="visible"
            exit={{ opacity: 0, x: -12, transition: { duration: 0.18 } }}
            className="space-y-4"
          >
            {loadingPackages ? (
              <div className="flex flex-col items-center justify-center py-16 text-xs text-slate-400">
                <Loader2 className="h-6 w-6 animate-spin text-slate-600 mb-2" />
                <span>Loading available studio packages…</span>
              </div>
            ) : packagesError ? (
              <div className="rounded-lg border border-red-200 bg-red-50 p-5 text-center text-xs text-red-700 space-y-3">
                <div className="flex items-center justify-center gap-2">
                  <AlertCircle className="h-4 w-4 text-red-600" />
                  <span className="font-semibold">{packagesError}</span>
                </div>
                <button
                  type="button"
                  onClick={fetchPackages}
                  className="inline-flex items-center gap-1.5 rounded bg-slate-900 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-slate-800 transition-colors"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  Retry Loading
                </button>
              </div>
            ) : packages.length === 0 ? (
              <div className="rounded-lg border border-dashed border-slate-200 p-8 text-center text-xs text-slate-500">
                No active packages currently available. Please check back shortly.
              </div>
            ) : (
              <>
                {packages.map((pkg) => (
                  <motion.button
                    key={pkg.id}
                    type="button"
                    whileHover={{ y: -2, transition: { duration: 0.15 } }}
                    whileTap={{ scale: 0.99 }}
                    onClick={() => setSelectedPackageId(pkg.id)}
                    className={`w-full text-left rounded-lg border p-5 transition-all ${
                      selectedPackageId === pkg.id
                        ? "border-slate-900 bg-slate-900 text-white"
                        : "border-slate-200 bg-white hover:border-slate-400"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-sm font-bold ${
                              selectedPackageId === pkg.id ? "text-white" : "text-slate-900"
                            }`}
                          >
                            {pkg.name}
                          </span>
                          {pkg.is_popular && (
                            <span
                              className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                                selectedPackageId === pkg.id
                                  ? "bg-white/20 text-white"
                                  : "bg-blue-50 text-blue-700"
                              }`}
                            >
                              Most Popular
                            </span>
                          )}
                        </div>
                        <p
                          className={`mt-1 text-xs ${
                            selectedPackageId === pkg.id ? "text-slate-300" : "text-slate-500"
                          }`}
                        >
                          {pkg.description}
                        </p>
                        <ul className="mt-2 space-y-1">
                          {(pkg.features || []).map((f) => (
                            <li key={f} className="flex items-center gap-1.5 text-xs">
                              <CheckCircle2
                                className={`h-3.5 w-3.5 shrink-0 ${
                                  selectedPackageId === pkg.id
                                    ? "text-emerald-400"
                                    : "text-emerald-500"
                                }`}
                              />
                              <span
                                className={
                                  selectedPackageId === pkg.id ? "text-slate-200" : "text-slate-600"
                                }
                              >
                                {f}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div className="shrink-0 text-right">
                        <p
                          className={`text-xl font-extrabold ${
                            selectedPackageId === pkg.id ? "text-white" : "text-slate-900"
                          }`}
                        >
                          ₹{Number(pkg.price_inr).toLocaleString("en-IN")}
                        </p>
                        <p
                          className={`text-[10px] ${
                            selectedPackageId === pkg.id ? "text-slate-300" : "text-slate-400"
                          }`}
                        >
                          {pkg.revisions_included} revision{pkg.revisions_included > 1 ? "s" : ""}
                        </p>
                      </div>
                    </div>
                  </motion.button>
                ))}

                <motion.button
                  type="button"
                  whileHover={{ scale: 1.005 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setStep(2)}
                  disabled={!selectedPackageId}
                  className="w-full flex items-center justify-center gap-2 rounded bg-slate-900 py-3 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50 transition-colors"
                >
                  Continue to Project Details
                  <ArrowRight className="h-4 w-4" />
                </motion.button>
              </>
            )}
          </motion.div>
        )}

        {/* Step 2: Project Details */}
        {step === 2 && (
          <motion.div
            key="step-2"
            variants={fadeUpVariants}
            initial="hidden"
            animate="visible"
            exit={{ opacity: 0, x: 12, transition: { duration: 0.18 } }}
            className="space-y-4"
          >
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-xs">
              <p className="text-slate-500">Selected package:</p>
              <p className="font-bold text-slate-900">
                {selectedPackage?.name} —{" "}
                ₹{(selectedPackage ? Number(selectedPackage.price_inr) : 0).toLocaleString("en-IN")}
              </p>
              <button
                type="button"
                onClick={() => setStep(1)}
                className="mt-1 text-blue-600 hover:underline font-semibold"
              >
                Change package
              </button>
            </div>

            <div className="space-y-4 rounded-lg border border-slate-200 bg-white p-5">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Project / Website Title *
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Dr. Sharma Clinic Website"
                  className="w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-slate-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Business / Brand Name *
                </label>
                <input
                  type="text"
                  value={businessName}
                  onChange={(e) => setBusinessName(e.target.value)}
                  placeholder="e.g. Sharma Multispecialty Clinic"
                  className="w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-slate-500 focus:outline-none"
                />
              </div>
            </div>

            <AnimatePresence>
              {error && (
                <motion.p
                  variants={alertVariants}
                  initial="hidden"
                  animate="visible"
                  exit="exit"
                  className="text-xs text-red-600 font-semibold"
                >
                  {error}
                </motion.p>
              )}
            </AnimatePresence>

            <div className="flex gap-3">
              <motion.button
                type="button"
                whileTap={{ scale: 0.98 }}
                onClick={() => setStep(1)}
                className="flex-1 rounded border border-slate-300 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
              >
                Back
              </motion.button>
              <motion.button
                type="button"
                whileTap={{ scale: 0.98 }}
                onClick={handleSubmit}
                disabled={submitting}
                className="flex-1 flex items-center justify-center gap-2 rounded bg-slate-900 py-2.5 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60 transition-colors"
              >
                {submitting ? (
                  <>
                    <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Creating…
                  </>
                ) : (
                  <>
                    Commission Project
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </motion.button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
