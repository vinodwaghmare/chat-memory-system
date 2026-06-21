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
  { href: "/health", label: "Health", icon: "❤️‍🩹" },
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
          {/* ── Sidebar ─────────────────────────────────── */}
          <nav className="w-60 min-h-screen glass-strong flex flex-col border-r border-white/[0.06] relative">
            {/* Subtle gradient line on right edge */}
            <div className="absolute right-0 top-0 bottom-0 w-px bg-gradient-to-b from-transparent via-blue-500/20 to-transparent" />

            {/* Brand */}
            <div className="px-5 py-6 mb-2">
              <div className="flex items-center gap-2.5">
                <span className="text-xl">🔮</span>
                <h1 className="text-lg font-bold gradient-text tracking-tight">
                  Memory System
                </h1>
              </div>
              <p className="text-[11px] text-gray-500 mt-1.5 pl-[34px]">
                Neural memory engine
              </p>
            </div>

            {/* Navigation */}
            <div className="flex flex-col gap-0.5 px-3 flex-1">
              {NAV_ITEMS.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="group relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-400 hover:text-white hover:bg-white/[0.04] transition-all duration-200"
                >
                  {/* Active indicator glow line */}
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-0 group-hover:h-5 rounded-full bg-gradient-to-b from-blue-400 to-purple-400 transition-all duration-200 opacity-0 group-hover:opacity-100 shadow-[0_0_8px_rgba(59,130,246,0.4)]" />
                  <span className="text-base">{item.icon}</span>
                  <span className="font-medium">{item.label}</span>
                </Link>
              ))}
            </div>

            {/* Bottom section */}
            <div className="px-5 py-4 border-t border-white/[0.04]">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse-glow" />
                <span className="text-[11px] text-gray-500">System online</span>
              </div>
            </div>
          </nav>

          {/* ── Main content ───────────────────────────── */}
          <main className="flex-1 p-8 overflow-auto">{children}</main>
        </div>
      </body>
    </html>
  );
}
