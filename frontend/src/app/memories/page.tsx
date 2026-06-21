"use client";

import { useEffect, useState } from "react";
import { fetchMemories } from "@/lib/api";
import type { Memory } from "@/lib/types";
import MemoryCard from "@/components/MemoryCard";

const TYPES = ["all", "semantic", "procedural", "episodic"] as const;

const TYPE_ICONS: Record<string, string> = {
  all: "🎯",
  semantic: "🔵",
  procedural: "🟣",
  episodic: "🟡",
};

export default function MemoriesPage() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [filter, setFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const type = filter === "all" ? undefined : filter;
    fetchMemories(undefined, type)
      .then(setMemories)
      .catch(() => setMemories([]))
      .finally(() => setLoading(false));
  }, [filter]);

  return (
    <div className="max-w-5xl animate-fade-in">
      {/* ── Header ───────────────────────────────────── */}
      <div className="flex items-end justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold">
            <span className="gradient-text">Memories</span>
          </h2>
          <p className="text-xs text-gray-500 mt-1">
            {memories.length} memor{memories.length === 1 ? "y" : "ies"} stored
          </p>
        </div>

        {/* ── Filter Tabs ────────────────────────────── */}
        <div className="flex gap-1.5">
          {TYPES.map((t) => (
            <button
              key={t}
              onClick={() => setFilter(t)}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium rounded-lg transition-all duration-300 ${
                filter === t
                  ? "bg-gradient-to-r from-blue-600/80 to-purple-600/80 text-white shadow-[0_0_15px_rgba(59,130,246,0.2)]"
                  : "glass text-gray-400 hover:text-white hover:bg-white/[0.04]"
              }`}
            >
              <span className="text-[11px]">{TYPE_ICONS[t]}</span>
              <span className="capitalize">{t}</span>
            </button>
          ))}
        </div>
      </div>

      {/* ── Content ──────────────────────────────────── */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="flex items-center gap-3 text-gray-500">
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-dot-bounce" />
            <span
              className="w-2 h-2 rounded-full bg-purple-400 animate-dot-bounce"
              style={{ animationDelay: "0.16s" }}
            />
            <span
              className="w-2 h-2 rounded-full bg-blue-400 animate-dot-bounce"
              style={{ animationDelay: "0.32s" }}
            />
            <span className="text-sm ml-2">Loading memories...</span>
          </div>
        </div>
      ) : memories.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <span className="text-5xl mb-4 opacity-30">🧠</span>
          <p className="text-sm">
            <span className="gradient-text font-medium">No memories found</span>
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Start a conversation to build memory
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          {memories.map((m) => (
            <MemoryCard key={m.id} memory={m} />
          ))}
        </div>
      )}
    </div>
  );
}
