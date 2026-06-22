"use client";

import { useEffect, useState } from "react";
import { fetchMemories } from "@/lib/api";
import type { Memory } from "@/lib/types";
import MemoryCard from "@/components/MemoryCard";
import { Brain } from "lucide-react";

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
    fetchMemories(type)
      .then(setMemories)
      .catch(() => setMemories([]))
      .finally(() => setLoading(false));
  }, [filter]);

  return (
    <div className="max-w-5xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-8">
        <div className="flex items-center gap-3">
          <Brain className="w-6 h-6 text-blue-400" />
          <h2 className="text-2xl font-bold text-white">
            Memories
          </h2>
          <p className="text-xs text-[#a3a3a3] mt-1">
            {memories.length} memor{memories.length === 1 ? "y" : "ies"} stored
          </p>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-1.5">
          {TYPES.map((t) => (
            <button
              key={t}
              onClick={() => setFilter(t)}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                filter === t
                  ? "bg-blue-600 text-white"
                  : "bg-[#2a2a2a] border border-[#404040] text-[#a3a3a3] hover:text-white hover:bg-[#333]"
              }`}
            >
              <span className="text-[11px]">{TYPE_ICONS[t]}</span>
              <span className="capitalize">{t}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <p className="text-[#a3a3a3] text-sm">Loading...</p>
        </div>
      ) : memories.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <span className="text-5xl mb-4">🧠</span>
          <p className="text-sm text-[#a3a3a3] font-medium">No memories found</p>
          <p className="text-xs text-[#666] mt-1">
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
