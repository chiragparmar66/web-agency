"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Globe,
  Home,
  LogOut,
  PlusCircle,
  Settings,
} from "lucide-react";
import { authStorage } from "@/lib/auth";
import { User } from "@/types";

interface SidebarProps {
  user: User | null;
  onCloseMobile?: () => void;
}

export default function Sidebar({ user, onCloseMobile }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = () => {
    authStorage.clear();
    router.push("/login");
  };

  const navItems = [
    {
      name: "Overview",
      href: "/dashboard",
      icon: Home,
    },
    {
      name: "Websites & Projects",
      href: "/dashboard/projects",
      icon: Globe,
    },
    {
      name: "Account Settings",
      href: "/dashboard/settings",
      icon: Settings,
    },
  ];

  return (
    <aside className="w-64 border-r border-slate-200 bg-white flex flex-col justify-between h-full">
      <div>
        {/* Studio Brand */}
        <div className="h-16 flex items-center gap-2 px-6 border-b border-slate-200">
          <div className="flex h-8 w-8 items-center justify-center rounded bg-slate-900 text-white font-bold text-xs">
            NX
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-bold tracking-tight text-slate-900">
              NEXUS PORTAL
            </span>
            <span className="text-[10px] text-slate-400 font-medium">
              Client Workspace
            </span>
          </div>
        </div>

        {/* User Card */}
        <div className="p-4 mx-3 my-4 rounded border border-slate-100 bg-slate-50">
          <p className="text-xs font-bold text-slate-900 truncate">
            {user?.full_name || "Client"}
          </p>
          <p className="text-[11px] text-slate-500 truncate mt-0.5">
            {user?.customer_profile?.company_name || user?.email || ""}
          </p>
          <div className="mt-2 inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-emerald-100 text-[10px] font-semibold text-emerald-800">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-600" />
            <span>Active Client Account</span>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="px-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={onCloseMobile}
                className={`flex items-center gap-3 px-3 py-2 rounded text-xs font-semibold transition-colors ${
                  isActive
                    ? "bg-slate-900 text-white"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? "text-white" : "text-slate-500"}`} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer / Logout */}
      <div className="p-4 border-t border-slate-200 space-y-2">
        <Link
          href="/"
          target="_blank"
          className="flex items-center gap-2 text-xs font-medium text-slate-500 hover:text-slate-900 px-2 py-1.5 transition-colors"
        >
          <span>View Public Studio Site &rarr;</span>
        </Link>
        <button
          type="button"
          onClick={handleLogout}
          className="w-full flex items-center gap-2 px-2 py-2 rounded text-xs font-semibold text-rose-600 hover:bg-rose-50 transition-colors"
        >
          <LogOut className="h-4 w-4" />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
}
