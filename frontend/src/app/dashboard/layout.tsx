"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Menu, X } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import Sidebar from "@/components/dashboard/Sidebar";
import { api, ApiError } from "@/lib/api";
import { authStorage } from "@/lib/auth";
import { User } from "@/types";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  useEffect(() => {
    const checkAuthAndLoadUser = async () => {
      const token = authStorage.getToken();
      if (!token) {
        router.push("/login");
        return;
      }

      try {
        const response = await api.get<User>("/auth/me");
        if (response.success && response.data) {
          setUser(response.data);
          authStorage.setUser(response.data);
        } else {
          authStorage.clear();
          router.push("/login");
        }
      } catch (err) {
        authStorage.clear();
        router.push("/login");
      } finally {
        setLoading(false);
      }
    };

    checkAuthAndLoadUser();
  }, [router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 text-slate-500 text-xs font-semibold">
        <div className="flex flex-col items-center gap-3">
          <div className="h-6 w-6 border-2 border-slate-300 border-t-slate-800 rounded-full animate-spin" />
          <span>Verifying client workspace session...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-slate-50 text-slate-900 overflow-x-hidden">
      {/* Desktop Sidebar */}
      <div className="hidden md:flex shrink-0">
        <Sidebar user={user} />
      </div>

      {/* Mobile Sidebar Drawer with AnimatePresence */}
      <AnimatePresence>
        {mobileSidebarOpen && (
          <div className="fixed inset-0 z-50 flex md:hidden">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 bg-slate-900/60"
              onClick={() => setMobileSidebarOpen(false)}
            />
            <motion.div
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
              className="relative flex w-64 max-w-xs flex-col bg-white shadow-xl z-10"
            >
              <div className="absolute top-2 right-2 p-1">
                <button
                  type="button"
                  onClick={() => setMobileSidebarOpen(false)}
                  className="p-1 rounded text-slate-500 hover:text-slate-800"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <Sidebar
                user={user}
                onCloseMobile={() => setMobileSidebarOpen(false)}
              />
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Main Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile Header Bar */}
        <header className="md:hidden flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded bg-slate-900 text-white font-bold text-xs">
              NX
            </div>
            <span className="text-sm font-bold text-slate-900">NEXUS PORTAL</span>
          </div>

          <button
            type="button"
            onClick={() => setMobileSidebarOpen(true)}
            className="p-2 rounded text-slate-700 hover:bg-slate-100"
            aria-label="Open sidebar"
          >
            <Menu className="h-5 w-5" />
          </button>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-4 sm:p-8 lg:p-10 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
