"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ArrowRight, CheckCircle2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { PricingPackage, ProjectItem } from "@/types";

const PACKAGES: PricingPackage[] = [
  {
    id: "",
    slug: "starter-website",
    name: "Starter Website",
    price_inr: 1999,
    description: "A clean single-page website for individual professionals.",
    features: ["Single-page responsive website", "Contact form", "SEO setup", "3-day delivery"],
    delivery_days: 3,
    revisions_included: 1,
  },
  {
    id: "",
    slug: "business-website",
    name: "Business Website",
    price_inr: 4999,
    description: "A professional multi-page website for established businesses.",
    features: ["Up to 5 pages", "Inquiry form", "Maps & social links", "7-day delivery"],
    delivery_days: 7,
    revisions_included: 2,
    is_popular: true,
  },
  {
    id: "",
    slug: "professional-website",
    name: "Professional Website",
    price_inr: 9999,
    description: "Premium site with blog, portfolio, and analytics.",
    features: ["Up to 10 pages", "Blog / news section", "Analytics integration", "12-day delivery"],
    delivery_days: 12,
    revisions_included: 3,
  },
  {
    id: "",
    slug: "custom-solution",
    name: "Custom Solution",
    price_inr: 19999,
    description: "Fully bespoke web app, e-commerce, or custom integration.",
    features: [
      "Unlimited pages",
      "Custom web features",
      "Payment integration",
      "Admin dashboard",
    ],
    delivery_days: 21,
    revisions_included: 5,
  },
];

export default function NewProjectPage() {
  const router = useRouter();
  const [step, setStep] = useState<1 | 2>(1);
  const [selectedPackageSlug, setSelectedPackageSlug] = useState<string>("business-website");
  const [title, setTitle] = useState("");
  const [businessName, setBusinessName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!title.trim() || !businessName.trim()) {
      setError("Please enter both a project title and business name.");
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const res = await api.post<ProjectItem>("/projects", {
        title: title.trim(),
        business_name: businessName.trim(),
        package_slug: selectedPackageSlug,
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
          Select a package and tell us about your business. Our team will contact you within 24 hours.
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

      {/* Step 1: Package Selection */}
      {step === 1 && (
        <div className="space-y-4">
          {PACKAGES.map((pkg) => (
            <button
              key={pkg.slug}
              type="button"
              onClick={() => setSelectedPackageSlug(pkg.slug)}
              className={`w-full text-left rounded-lg border p-5 transition-all ${
                selectedPackageSlug === pkg.slug
                  ? "border-slate-900 bg-slate-900 text-white"
                  : "border-slate-200 bg-white hover:border-slate-400"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-sm font-bold ${
                        selectedPackageSlug === pkg.slug ? "text-white" : "text-slate-900"
                      }`}
                    >
                      {pkg.name}
                    </span>
                    {pkg.is_popular && (
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                          selectedPackageSlug === pkg.slug
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
                      selectedPackageSlug === pkg.slug ? "text-slate-300" : "text-slate-500"
                    }`}
                  >
                    {pkg.description}
                  </p>
                  <ul className="mt-2 space-y-1">
                    {pkg.features.map((f) => (
                      <li key={f} className="flex items-center gap-1.5 text-xs">
                        <CheckCircle2
                          className={`h-3.5 w-3.5 shrink-0 ${
                            selectedPackageSlug === pkg.slug
                              ? "text-emerald-400"
                              : "text-emerald-500"
                          }`}
                        />
                        <span
                          className={
                            selectedPackageSlug === pkg.slug ? "text-slate-200" : "text-slate-600"
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
                      selectedPackageSlug === pkg.slug ? "text-white" : "text-slate-900"
                    }`}
                  >
                    ₹{pkg.price_inr.toLocaleString("en-IN")}
                  </p>
                  <p
                    className={`text-[10px] ${
                      selectedPackageSlug === pkg.slug ? "text-slate-300" : "text-slate-400"
                    }`}
                  >
                    {pkg.revisions_included} revision{pkg.revisions_included > 1 ? "s" : ""}
                  </p>
                </div>
              </div>
            </button>
          ))}

          <button
            type="button"
            onClick={() => setStep(2)}
            className="w-full flex items-center justify-center gap-2 rounded bg-slate-900 py-3 text-sm font-semibold text-white hover:bg-slate-800 transition-colors"
          >
            Continue to Project Details
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Step 2: Project Details */}
      {step === 2 && (
        <div className="space-y-4">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-xs">
            <p className="text-slate-500">Selected package:</p>
            <p className="font-bold text-slate-900">
              {PACKAGES.find((p) => p.slug === selectedPackageSlug)?.name} —{" "}
              ₹{(PACKAGES.find((p) => p.slug === selectedPackageSlug)?.price_inr ?? 0).toLocaleString("en-IN")}
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

          {error && (
            <p className="text-xs text-red-600 font-semibold">{error}</p>
          )}

          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => setStep(1)}
              className="flex-1 rounded border border-slate-300 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
            >
              Back
            </button>
            <button
              type="button"
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
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
