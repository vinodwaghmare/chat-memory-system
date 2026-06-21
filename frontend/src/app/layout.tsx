import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Chat Memory System",
  description: "Memory dashboard for the ChatGPT-style memory system",
};

const NAV_ITEMS = [
  { href: "/", label: "Dashboard" },
  { href: "/memories", label: "Memories" },
  { href: "/conversations", label: "Chat" },
  { href: "/health", label: "Health" },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <div className="flex">
          <nav className="w-56 min-h-screen bg-gray-900 border-r border-gray-800 p-4 flex flex-col gap-1">
            <h1 className="text-lg font-bold text-white mb-6 px-3">
              Memory System
            </h1>
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="px-3 py-2 rounded-md text-sm text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <main className="flex-1 p-6">{children}</main>
        </div>
      </body>
    </html>
  );
}
