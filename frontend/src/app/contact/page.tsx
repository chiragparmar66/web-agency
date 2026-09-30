"use client";

import { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  ArrowRight,
  CheckCircle2,
  Clock,
  Mail,
  MapPin,
  MessageSquare,
  Phone,
  Send,
} from "lucide-react";
import Link from "next/link";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import { api, ApiError } from "@/lib/api";
import { APP_CONFIG } from "@/lib/constants";

function ContactForm() {
  const searchParams = useSearchParams();
  const preselectedService = searchParams.get("service") || "";

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    business_name: "",
    business_type: "",
    city: "",
    selected_package: preselectedService,
    message: "",
  });

  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMessage(null);

    try {
      const response = await api.post("/inquiries", {
        ...formData,
        source: "CONTACT_FORM",
      });

      if (response.success) {
        setSuccess(true);
        setFormData({
          name: "",
          email: "",
          phone: "",
          business_name: "",
          business_type: "",
          city: "",
          selected_package: "",
          message: "",
        });
      }
    } catch (err: any) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Unable to submit inquiry. Please try again or reach out on WhatsApp.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-900">
      <Navbar />

      <main className="flex-1">
        {/* Header */}
        <section className="border-b border-slate-200 bg-white py-16 sm:py-20">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="max-w-3xl">
              <span className="text-xs font-bold uppercase tracking-wider text-blue-600">
                Contact & Inquiries
              </span>
              <h1 className="mt-3 text-4xl sm:text-5xl font-extrabold tracking-tight text-slate-900">
                Initiate a project consultation with our studio.
              </h1>
              <p className="mt-4 text-base sm:text-lg text-slate-600 leading-relaxed">
                Whether you need a bespoke corporate website, high-converting landing page, or complex custom web application, our engineers are ready to discuss your specifications.
              </p>
            </div>
          </div>
        </section>

        {/* Form and Contact Information Section */}
        <section className="py-16 sm:py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
              {/* Form Column */}
              <div className="lg:col-span-7 bg-white rounded-lg border border-slate-200 p-8 sm:p-10 shadow-sm">
                <h2 className="text-xl font-bold text-slate-900 mb-2">
                  Project Inquiry Form
                </h2>
                <p className="text-xs text-slate-500 mb-8">
                  Fill in your project essentials below. We reply with initial architectural thoughts within 1 business day.
                </p>

                {success ? (
                  <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-8 text-center space-y-4">
                    <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
                      <CheckCircle2 className="h-6 w-6" />
                    </div>
                    <h3 className="text-lg font-bold text-emerald-900">
                      Inquiry Received Successfully
                    </h3>
                    <p className="text-xs text-emerald-700 max-w-md mx-auto leading-relaxed">
                      Thank you for contacting Nexus Studio. An engineer will review your requirements and reach out via email or phone shortly.
                    </p>
                    <button
                      type="button"
                      onClick={() => setSuccess(false)}
                      className="mt-4 inline-flex items-center gap-2 rounded bg-emerald-800 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-900"
                    >
                      Submit Another Inquiry
                    </button>
                  </div>
                ) : (
                  <form onSubmit={handleSubmit} className="space-y-6 text-sm">
                    {errorMessage && (
                      <div className="rounded bg-rose-50 border border-rose-200 p-3.5 text-xs text-rose-700 font-medium">
                        {errorMessage}
                      </div>
                    )}

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                          Full Name <span className="text-rose-500">*</span>
                        </label>
                        <input
                          type="text"
                          required
                          value={formData.name}
                          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                          placeholder="e.g. Anand Mahindra"
                          className="w-full rounded border border-slate-300 px-3.5 py-2.5 text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                          Email Address
                        </label>
                        <input
                          type="email"
                          value={formData.email}
                          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                          placeholder="anand@company.in"
                          className="w-full rounded border border-slate-300 px-3.5 py-2.5 text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                          Phone / WhatsApp <span className="text-rose-500">*</span>
                        </label>
                        <input
                          type="tel"
                          required
                          value={formData.phone}
                          onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                          placeholder="+91 98765 43210"
                          className="w-full rounded border border-slate-300 px-3.5 py-2.5 text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                          City / State
                        </label>
                        <input
                          type="text"
                          value={formData.city}
                          onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                          placeholder="e.g. Pune, Maharashtra"
                          className="w-full rounded border border-slate-300 px-3.5 py-2.5 text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                          Company / Brand Name
                        </label>
                        <input
                          type="text"
                          value={formData.business_name}
                          onChange={(e) => setFormData({ ...formData, business_name: e.target.value })}
                          placeholder="e.g. Apex Industrial Solutions"
                          className="w-full rounded border border-slate-300 px-3.5 py-2.5 text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                          Industry / Business Type
                        </label>
                        <input
                          type="text"
                          value={formData.business_type}
                          onChange={(e) => setFormData({ ...formData, business_type: e.target.value })}
                          placeholder="e.g. Healthcare, Legal, Manufacturing"
                          className="w-full rounded border border-slate-300 px-3.5 py-2.5 text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                        Selected Service or Scope
                      </label>
                      <select
                        value={formData.selected_package}
                        onChange={(e) => setFormData({ ...formData, selected_package: e.target.value })}
                        className="w-full rounded border border-slate-300 px-3.5 py-2.5 text-slate-900 bg-white focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600"
                      >
                        <option value="">General Project Consultation</option>
                        <option value="business-websites">Bespoke Business Website</option>
                        <option value="landing-pages">High-Converting Landing Page</option>
                        <option value="portfolio-websites">Studio & Portfolio Website</option>
                        <option value="ecommerce-websites">E-Commerce Platform</option>
                        <option value="website-maintenance">Maintenance & Performance Retainer</option>
                        <option value="custom-web-apps">Custom Web Application</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                        Project Brief / Requirements <span className="text-rose-500">*</span>
                      </label>
                      <textarea
                        required
                        rows={4}
                        value={formData.message}
                        onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                        placeholder="Describe your current business, project goals, required pages, reference websites you admire, and target launch timeframe..."
                        className="w-full rounded border border-slate-300 px-3.5 py-2.5 text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600"
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={loading}
                      className="w-full inline-flex items-center justify-center gap-2 rounded bg-slate-900 px-6 py-3 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50 transition-colors shadow-sm"
                    >
                      {loading ? (
                        <span>Submitting Inquiry...</span>
                      ) : (
                        <>
                          <Send className="h-4 w-4" />
                          <span>Submit Project Inquiry</span>
                        </>
                      )}
                    </button>
                  </form>
                )}
              </div>

              {/* Sidebar Contact Info */}
              <div className="lg:col-span-5 space-y-6">
                {/* Fast-track WhatsApp Box */}
                <div className="rounded-lg border border-emerald-200 bg-emerald-50/60 p-6 space-y-4">
                  <div className="flex items-center gap-2.5 text-emerald-800 font-bold text-sm">
                    <MessageSquare className="h-5 w-5 text-emerald-600" />
                    <span>Fast-Track WhatsApp Consultation</span>
                  </div>
                  <p className="text-xs text-emerald-700 leading-relaxed">
                    Prefer direct messaging? Send your requirements, business name, and reference websites directly to our developer team on WhatsApp for an immediate response.
                  </p>
                  <a
                    href={`https://wa.me/${APP_CONFIG.whatsappNumber.replace(/[^0-9]/g, "")}?text=${encodeURIComponent(
                      "Hello Nexus Studio! I would like to discuss a new web development project."
                    )}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 rounded bg-emerald-700 px-4 py-2.5 text-xs font-semibold text-white hover:bg-emerald-800 transition-colors"
                  >
                    <span>Message on WhatsApp</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </a>
                </div>

                {/* Studio Office & Direct Details */}
                <div className="rounded-lg border border-slate-200 bg-white p-6 space-y-6">
                  <h3 className="font-bold text-slate-900 text-sm">
                    Studio Communications
                  </h3>

                  <div className="space-y-4 text-xs text-slate-600">
                    <div className="flex items-start gap-3">
                      <MapPin className="h-4 w-4 text-slate-500 shrink-0 mt-0.5" />
                      <div>
                        <strong className="text-slate-800">Primary Locations:</strong>
                        <p className="text-slate-500 mt-0.5">Bengaluru & Mumbai, India</p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3">
                      <Mail className="h-4 w-4 text-slate-500 shrink-0 mt-0.5" />
                      <div>
                        <strong className="text-slate-800">Email:</strong>
                        <p className="mt-0.5">
                          <a
                            href={`mailto:${APP_CONFIG.supportEmail}`}
                            className="text-blue-600 hover:underline"
                          >
                            {APP_CONFIG.supportEmail}
                          </a>
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3">
                      <Phone className="h-4 w-4 text-slate-500 shrink-0 mt-0.5" />
                      <div>
                        <strong className="text-slate-800">Direct Phone:</strong>
                        <p className="mt-0.5 text-slate-700">{APP_CONFIG.whatsappNumber}</p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3">
                      <Clock className="h-4 w-4 text-slate-500 shrink-0 mt-0.5" />
                      <div>
                        <strong className="text-slate-800">Business Hours:</strong>
                        <p className="text-slate-500 mt-0.5">Monday &ndash; Saturday, 9:30 AM &ndash; 7:30 PM IST</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Client Portal Link */}
                <div className="rounded-lg border border-slate-200 bg-slate-100 p-6 text-xs text-slate-600 space-y-2">
                  <h4 className="font-semibold text-slate-800">Existing Clients</h4>
                  <p className="text-slate-500">
                    Already commissioned a website with us? Sign in to your Customer Portal to track staging previews, request revisions, and manage deployments.
                  </p>
                  <Link
                    href="/login"
                    className="inline-flex items-center text-blue-600 font-semibold hover:underline pt-1"
                  >
                    <span>Sign in to Customer Dashboard &rarr;</span>
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}

export default function ContactPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-slate-50 text-slate-500 text-xs font-semibold">
          <div className="flex flex-col items-center gap-3">
            <div className="h-6 w-6 border-2 border-slate-300 border-t-slate-800 rounded-full animate-spin" />
            <span>Loading contact portal...</span>
          </div>
        </div>
      }
    >
      <ContactForm />
    </Suspense>
  );
}

