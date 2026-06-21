import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Chat Memory System",
  description: "Memory dashboard for the ChatGPT-style memory system",
};

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: "📊" },
  { href: "/memories", label: "Memories", icon: "🧠" },
  { href: "/conversations", label: "Chat", icon: "💬" },
  { href: "/health", label: "Health", icon: "❤️" },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className={`${inter.className} min-h-screen antialiased`}>
        <div className="flex">
          {/* Sidebar */}
          <nav className="w-60 min-h-screen bg-[#1f1f1f] flex flex-col border-r border-[#2e2e2e]">
            {/* Brand */}
            <div className="px-5 py-6 mb-2">
              <div className="flex items-center gap-2.5">
                <span className="text-xl">🧠</span>
                <h1 className="text-lg font-bold text-white tracking-tight">
                  Memory System
                </h1>
              </div>
              <p className="text-[11px] text-[#a3a3a3] mt-1.5 pl-[34px]">
                Neural memory engine
              </p>
            </div>

            {/* Navigation */}
            <div className="flex flex-col gap-0.5 px-3 flex-1">
              {NAV_ITEMS.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-[#a3a3a3] hover:bg-[#2a2a2a] hover:text-white transition-colors"
                >
                  <span className="text-base">{item.icon}</span>
                  <span className="font-medium">{item.label}</span>
                </Link>
              ))}
            </div>
          </nav>

          {/* Main content */}
          <main className="flex-1 p-8 overflow-auto">{children}</main>
        </div>
      </body>
    </html>
  );
}
