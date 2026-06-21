"use client";

import { useEffect, useState } from "react";
import { fetchMemories } from "@/lib/api";
import type { Memory } from "@/lib/types";
import MemoryCard from "@/components/MemoryCard";

const TYPES = ["all", "semantic", "procedural", "episodic"] as const;

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
    <div className="max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Memories</h2>
        <div className="flex gap-1">
          {TYPES.map((t) => (
            <button
              key={t}
              onClick={() => setFilter(t)}
              className={`px-3 py-1 text-xs rounded-md border ${
                filter === t
                  ? "bg-blue-600 border-blue-500 text-white"
                  : "bg-gray-900 border-gray-700 text-gray-400 hover:text-white"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <p className="text-gray-500 text-sm">Loading...</p>
      ) : memories.length === 0 ? (
        <p className="text-gray-500 text-sm">
          No memories found. Start a conversation to build memory.
        </p>
      ) : (
        <div className="space-y-3">
          {memories.map((m) => (
            <MemoryCard key={m.id} memory={m} />
          ))}
        </div>
      )}
    </div>
  );
}
