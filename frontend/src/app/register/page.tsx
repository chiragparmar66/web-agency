"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Building, Lock, Mail, Phone, ShieldAlert, User } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import { api, ApiError } from "@/lib/api";
import { authStorage } from "@/lib/auth";
import { fadeUpVariants, alertVariants } from "@/lib/motion";

export default function RegisterPage() {
  const router = useRouter();

  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    phone: "",
    password: "",
    company_name: "",
    business_type: "",
    city: "",
  });

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMessage(null);

    // Client-side quick password validation matching backend constraints
    if (formData.password.length < 8) {
      setErrorMessage("Password must be at least 8 characters long.");
      setLoading(false);
      return;
    }

    try {
      const response = await api.post<any>("/auth/register", formData);

      if (response.success && response.data?.access_token) {
        authStorage.setTokens(
          response.data.access_token,
          response.data.refresh_token
        );
        authStorage.setUser(response.data.user);
        router.push("/dashboard");
      } else {
        setErrorMessage("Registration failed. Please check the provided information.");
      }
    } catch (err: any) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Unable to connect to authentication server. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-900">
      <Navbar />

      <main className="flex-1 flex items-center justify-center py-16 px-4 sm:px-6 lg:px-8">
        <motion.div
          variants={fadeUpVariants}
          initial="hidden"
          animate="visible"
          className="w-full max-w-lg space-y-8 bg-white border border-slate-200 rounded-lg p-8 sm:p-10 shadow-sm"
        >
          <div className="text-center">
            <div className="mx-auto flex h-10 w-10 items-center justify-center rounded bg-slate-900 text-white font-bold text-sm">
              NX
            </div>
            <h1 className="mt-4 text-2xl font-bold tracking-tight text-slate-900">
              Create Client Account
            </h1>
            <p className="mt-2 text-xs text-slate-500">
              Register to initiate projects, track build progress, and request revisions.
            </p>
          </div>

          <AnimatePresence mode="wait">
            {errorMessage && (
              <motion.div
                variants={alertVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                className="rounded bg-rose-50 border border-rose-200 p-3.5 flex items-start gap-2.5 text-xs text-rose-700"
              >
                <ShieldAlert className="h-4 w-4 shrink-0 mt-0.5 text-rose-600" />
                <span>{errorMessage}</span>
              </motion.div>
            )}
          </AnimatePresence>

          <form onSubmit={handleRegister} className="space-y-4 text-sm">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Full Name <span className="text-rose-500">*</span>
              </label>
              <div className="relative">
                <input
                  type="text"
                  required
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  placeholder="e.g. Vikram Singhania"
                  className="w-full rounded border border-slate-300 pl-10 pr-3.5 py-2 text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600 text-sm"
                />
                <User className="h-4 w-4 text-slate-400 absolute left-3.5 top-2.5" />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Email Address <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="vikram@enterprise.in"
                    className="w-full rounded border border-slate-300 pl-10 pr-3.5 py-2 text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600 text-sm"
                  />
                  <Mail className="h-4 w-4 text-slate-400 absolute left-3.5 top-2.5" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Phone Number <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <input
                    type="tel"
                    required
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    placeholder="+91 98765 43210"
                    className="w-full rounded border border-slate-300 pl-10 pr-3.5 py-2 text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600 text-sm"
                  />
                  <Phone className="h-4 w-4 text-slate-400 absolute left-3.5 top-2.5" />
                </div>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Password <span className="text-rose-500">*</span>
              </label>
              <div className="relative">
                <input
                  type="password"
                  required
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  placeholder="Min. 8 chars (uppercase, lowercase, number)"
                  className="w-full rounded border border-slate-300 pl-10 pr-3.5 py-2 text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600 text-sm"
                />
                <Lock className="h-4 w-4 text-slate-400 absolute left-3.5 top-2.5" />
              </div>
              <p className="mt-1 text-[11px] text-slate-500">
                Must contain at least 8 characters, with uppercase, lowercase, and a number or symbol.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Company / Brand Name
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={formData.company_name}
                    onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                    placeholder="e.g. Singhania Logistics"
                    className="w-full rounded border border-slate-300 pl-10 pr-3.5 py-2 text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600 text-sm"
                  />
                  <Building className="h-4 w-4 text-slate-400 absolute left-3.5 top-2.5" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  City
                </label>
                <input
                  type="text"
                  value={formData.city}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                  placeholder="e.g. Hyderabad"
                  className="w-full rounded border border-slate-300 px-3.5 py-2 text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600 text-sm"
                />
              </div>
            </div>

            <div className="pt-2">
              <motion.button
                type="submit"
                disabled={loading}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.98 }}
                className="w-full inline-flex items-center justify-center gap-2 rounded bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50 transition-colors shadow-sm"
              >
                {loading ? (
                  <span>Creating Account...</span>
                ) : (
                  <>
                    <span>Complete Registration</span>
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </motion.button>
            </div>
          </form>

          <div className="pt-4 border-t border-slate-100 text-center text-xs text-slate-500">
            <span>Already have an account? </span>
            <Link
              href="/login"
              className="font-semibold text-blue-600 hover:text-blue-700 hover:underline"
            >
              Sign In
            </Link>
          </div>
        </motion.div>
      </main>

      <Footer />
    </div>
  );
}
