"use client";

import type { Memory } from "@/lib/types";
import Link from "next/link";

const TYPE_CONFIG: Record<string, { badge: string; bar: string; icon: string }> = {
  semantic: {
    badge: "bg-blue-500/15 text-blue-400 border border-blue-500/25",
    bar: "bg-blue-500",
    icon: "🔵",
  },
  procedural: {
    badge: "bg-purple-500/15 text-purple-400 border border-purple-500/25",
    bar: "bg-purple-500",
    icon: "🟣",
  },
  episodic: {
    badge: "bg-amber-500/15 text-amber-400 border border-amber-500/25",
    bar: "bg-amber-500",
    icon: "🟡",
  },
};

export default function MemoryCard({ memory }: { memory: Memory }) {
  const config = TYPE_CONFIG[memory.type] || {
    badge: "bg-gray-500/15 text-gray-400 border border-gray-500/25",
    bar: "bg-gray-500",
    icon: "⚪",
  };

  return (
    <Link href={`/memories/${memory.id}`}>
      <div className="bg-[#262626] border border-[#333] rounded-xl p-4 hover:border-[#555] transition-colors cursor-pointer">
        <div className="flex items-center gap-2.5 mb-3">
          <span className="text-sm">{config.icon}</span>
          <span
            className={`text-[11px] font-medium px-2.5 py-0.5 rounded-full ${config.badge}`}
          >
            {memory.type}
          </span>

          {/* Importance mini bar */}
          <div className="flex items-center gap-1.5 ml-auto">
            <span className="text-[10px] text-[#a3a3a3]">
              {memory.importance}/10
            </span>
            <div className="w-16 h-1.5 rounded-full bg-[#333] overflow-hidden">
              <div
                className={`h-full rounded-full ${config.bar}`}
                style={{ width: `${(memory.importance / 10) * 100}%` }}
              />
            </div>
          </div>
        </div>

        <p className="text-sm text-[#e5e5e5] leading-relaxed">
          {memory.content}
        </p>

        <div className="flex items-center gap-4 mt-3 text-[11px] text-[#a3a3a3]">
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
