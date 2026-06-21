"use client";

import type { Memory } from "@/lib/types";
import Link from "next/link";

const TYPE_CONFIG: Record<string, { badge: string; glow: string; bar: string; icon: string }> = {
  semantic: {
    badge: "bg-blue-500/10 text-blue-300 border-blue-500/20",
    glow: "hover:shadow-[0_0_25px_rgba(59,130,246,0.12)]",
    bar: "bg-gradient-to-r from-blue-500 to-cyan-400",
    icon: "🔵",
  },
  procedural: {
    badge: "bg-purple-500/10 text-purple-300 border-purple-500/20",
    glow: "hover:shadow-[0_0_25px_rgba(167,139,250,0.12)]",
    bar: "bg-gradient-to-r from-purple-500 to-pink-400",
    icon: "🟣",
  },
  episodic: {
    badge: "bg-amber-500/10 text-amber-300 border-amber-500/20",
    glow: "hover:shadow-[0_0_25px_rgba(245,158,11,0.12)]",
    bar: "bg-gradient-to-r from-amber-500 to-orange-400",
    icon: "🟡",
  },
};

export default function MemoryCard({ memory }: { memory: Memory }) {
  const config = TYPE_CONFIG[memory.type] || {
    badge: "bg-gray-500/10 text-gray-300 border-gray-500/20",
    glow: "",
    bar: "bg-gray-500",
    icon: "⚪",
  };

  return (
    <Link href={`/memories/${memory.id}`}>
      <div
        className={`glass rounded-xl p-5 hover:bg-white/[0.04] hover:-translate-y-0.5 transition-all duration-300 cursor-pointer group ${config.glow}`}
      >
        <div className="flex items-center gap-2.5 mb-3">
          <span className="text-sm">{config.icon}</span>
          <span
            className={`text-[11px] font-medium px-2.5 py-0.5 rounded-full border ${config.badge}`}
          >
            {memory.type}
          </span>

          {/* ── Importance mini bar ──────────────────── */}
          <div className="flex items-center gap-1.5 ml-auto">
            <span className="text-[10px] text-gray-500">
              {memory.importance}/10
            </span>
            <div className="w-16 h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
              <div
                className={`h-full rounded-full ${config.bar} transition-all duration-500`}
                style={{ width: `${(memory.importance / 10) * 100}%` }}
              />
            </div>
          </div>
        </div>

        <p className="text-sm text-gray-200 leading-relaxed group-hover:text-white transition-colors">
          {memory.content}
        </p>

        <div className="flex items-center gap-4 mt-3 text-[11px] text-gray-500">
          <span className="flex items-center gap-1">
            <span className="opacity-60">⚡</span>
            {(memory.confidence * 100).toFixed(0)}% conf
          </span>
          <span>wt: {memory.weight.toFixed(2)}</span>
          <span>used {memory.reinforcement_count}x</span>
          {memory.created_at && (
            <span className="ml-auto">
              {new Date(memory.created_at).toLocaleDateString()}
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
