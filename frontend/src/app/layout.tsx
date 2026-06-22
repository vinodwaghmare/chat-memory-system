import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import { LayoutDashboard, Brain, MessageSquare, Activity } from "lucide-react";
import MobileNav from "@/components/MobileNav";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Chat Memory System",
  description: "Memory dashboard for the ChatGPT-style memory system",
  viewport: "width=device-width, initial-scale=1",
};

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/memories", label: "Memories", icon: Brain },
  { href: "/conversations", label: "Chat", icon: MessageSquare },
  { href: "/health", label: "Health", icon: Activity },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className={`${inter.className} min-h-screen antialiased`}>
        {/* Mobile nav */}
        <MobileNav />

        <div className="flex">
          {/* Desktop sidebar - hidden on mobile */}
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
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-[#a3a3a3] hover:bg-[#2a2a2a] hover:text-white transition-colors"
                  >
                    <Icon className="w-4 h-4" />
                    <span className="font-medium">{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </nav>

          {/* Main content */}
          <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-auto min-h-screen">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
