"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { LayoutDashboard, Brain, MessageSquare, Activity, LogOut } from "lucide-react";
import { isLoggedIn, logout, getUser, type AuthUser } from "@/lib/api";
import MobileNav from "./MobileNav";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/memories", label: "Memories", icon: Brain },
  { href: "/conversations", label: "Chat", icon: MessageSquare },
  { href: "/health", label: "Health", icon: Activity },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);
  const [user, setUser] = useState<AuthUser | null>(null);

  const isLoginPage = pathname === "/login";

  useEffect(() => {
    if (isLoginPage) {
      setReady(true);
      return;
    }
    if (!isLoggedIn()) {
      router.replace("/login");
      return;
    }
    setReady(true);
    getUser().then(setUser).catch(() => {});
  }, [pathname, router, isLoginPage]);

  if (isLoginPage) {
    return <>{children}</>;
  }

  if (!ready) return null;

  function handleLogout() {
    logout();
    router.replace("/login");
  }

  return (
    <>
      <MobileNav user={user} onLogout={handleLogout} />

      <div className="flex">
        {/* Desktop sidebar */}
        <nav className="hidden lg:flex w-60 min-h-screen bg-[#1f1f1f] flex-col border-r border-[#2e2e2e] sticky top-0 h-screen">
          <div className="px-5 py-6 mb-2">
            <div className="flex items-center gap-2.5">
              <Brain className="w-5 h-5 text-blue-400" />
              <h1 className="text-lg font-bold text-white tracking-tight">
                Memory System
              </h1>
            </div>
            <p className="text-[11px] text-[#a3a3a3] mt-1.5 pl-[30px]">
              Neural memory engine
            </p>
          </div>

          <div className="flex flex-col gap-0.5 px-3 flex-1">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
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

          {/* User + Logout */}
          <div className="px-3 py-4 border-t border-[#2e2e2e]">
            {user && (
              <div className="flex items-center gap-2.5 px-3 py-2 mb-2">
                {user.picture ? (
                  <img src={user.picture} alt="" className="w-7 h-7 rounded-full" />
                ) : (
                  <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-xs text-white font-medium">
                    {(user.name || user.email)[0].toUpperCase()}
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-white truncate">{user.name || user.email}</p>
                  <p className="text-[10px] text-[#666] truncate">{user.email}</p>
                </div>
              </div>
            )}
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-[#a3a3a3] hover:bg-[#2a2a2a] hover:text-white transition-colors w-full"
            >
              <LogOut className="w-4 h-4" />
              <span className="font-medium">Sign Out</span>
            </button>
          </div>
        </nav>

        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-auto min-h-screen">
          {children}
        </main>
      </div>
    </>
  );
}
