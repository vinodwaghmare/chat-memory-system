"use client";

import type { Memory } from "@/lib/types";
import Link from "next/link";

const TYPE_COLORS: Record<string, string> = {
  semantic: "bg-blue-900/50 text-blue-300 border-blue-700",
  procedural: "bg-purple-900/50 text-purple-300 border-purple-700",
  episodic: "bg-amber-900/50 text-amber-300 border-amber-700",
};

export default function MemoryCard({ memory }: { memory: Memory }) {
  const color = TYPE_COLORS[memory.type] || "bg-gray-800 text-gray-300";

  return (
    <Link href={`/memories/${memory.id}`}>
      <div className="border border-gray-800 rounded-lg p-4 hover:border-gray-600 transition-colors cursor-pointer">
        <div className="flex items-center gap-2 mb-2">
          <span className={`text-xs px-2 py-0.5 rounded border ${color}`}>
            {memory.type}
          </span>
          <span className="text-xs text-gray-500">
            importance: {memory.importance}/10
          </span>
          <span className="text-xs text-gray-500">
            confidence: {(memory.confidence * 100).toFixed(0)}%
          </span>
        </div>
        <p className="text-sm text-gray-200">{memory.content}</p>
        <div className="flex gap-4 mt-2 text-xs text-gray-500">
          <span>weight: {memory.weight.toFixed(2)}</span>
          <span>used: {memory.reinforcement_count}x</span>
          {memory.created_at && (
            <span>{new Date(memory.created_at).toLocaleDateString()}</span>
          )}
        </div>
      </div>
    </Link>
  );
}
