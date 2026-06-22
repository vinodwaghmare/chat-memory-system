"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Brain, MessageSquare, Activity, Menu, X, LogOut } from "lucide-react";
import type { AuthUser } from "@/lib/api";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/memories", label: "Memories", icon: Brain },
  { href: "/conversations", label: "Chat", icon: MessageSquare },
  { href: "/health", label: "Health", icon: Activity },
];

export default function MobileNav({
  user,
  onLogout,
}: {
  user?: AuthUser | null;
  onLogout?: () => void;
}) {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  return (
    <>
      <div className="lg:hidden flex items-center justify-between px-4 py-3 bg-[#1f1f1f] border-b border-[#2e2e2e]">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-blue-400" />
          <span className="text-sm font-bold text-white">Memory System</span>
        </div>
        <button
          onClick={() => setOpen(!open)}
          className="text-[#a3a3a3] hover:text-white p-1"
        >
          {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {open && (
        <div className="lg:hidden fixed inset-0 z-50 bg-black/50" onClick={() => setOpen(false)}>
          <div
            className="w-64 h-full bg-[#1f1f1f] border-r border-[#2e2e2e] p-4 flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-2 mb-6 px-2">
              <Brain className="w-5 h-5 text-blue-400" />
              <span className="text-lg font-bold text-white">Memory System</span>
            </div>
            <div className="flex flex-col gap-0.5 flex-1">
              {NAV_ITEMS.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setOpen(false)}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                      isActive
                        ? "bg-[#2a2a2a] text-white"
                        : "text-[#a3a3a3] hover:bg-[#2a2a2a] hover:text-white"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="font-medium">{item.label}</span>
                  </Link>
                );
              })}
            </div>

            {user && (
              <div className="border-t border-[#2e2e2e] pt-3">
                <div className="flex items-center gap-2 px-3 py-2 mb-2">
                  {user.picture ? (
                    <img src={user.picture} alt="" className="w-6 h-6 rounded-full" />
                  ) : (
                    <div className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center text-[10px] text-white font-medium">
                      {(user.name || user.email)[0].toUpperCase()}
                    </div>
                  )}
                  <span className="text-xs text-white truncate">{user.name || user.email}</span>
                </div>
                {onLogout && (
                  <button
                    onClick={() => { setOpen(false); onLogout(); }}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-[#a3a3a3] hover:bg-[#2a2a2a] hover:text-white transition-colors w-full"
                  >
                    <LogOut className="w-4 h-4" />
                    <span className="font-medium">Sign Out</span>
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
