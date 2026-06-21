"use client";

import { useEffect, useState } from "react";
import { fetchMemories, fetchHealth } from "@/lib/api";
import type { Memory, HealthStatus } from "@/lib/types";
import HealthBadge from "@/components/HealthBadge";
import Link from "next/link";

export default function DashboardPage() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchMemories()
      .then(setMemories)
      .catch(() => setError("Backend not reachable"));
    fetchHealth()
      .then(setHealth)
      .catch(() => {});
  }, []);

  const byType = {
    semantic: memories.filter((m) => m.type === "semantic").length,
    procedural: memories.filter((m) => m.type === "procedural").length,
    episodic: memories.filter((m) => m.type === "episodic").length,
  };

  return (
    <div className="max-w-4xl">
      <h2 className="text-2xl font-bold mb-6">Dashboard</h2>

      {error && (
        <div className="bg-red-900/30 border border-red-800 rounded-md p-3 mb-6 text-sm text-red-300">
          {error} — start the backend with{" "}
          <code className="bg-gray-800 px-1 rounded">
            uvicorn backend.main:app --port 8001
          </code>
        </div>
      )}

      {health && (
        <div className="mb-6">
          <h3 className="text-sm text-gray-400 mb-2">
            Services — v{health.version}
          </h3>
          <div className="flex gap-3">
            {Object.entries(health.services).map(([name, status]) => (
              <HealthBadge key={name} name={name} status={status} />
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-3xl font-bold text-blue-400">{memories.length}</p>
          <p className="text-xs text-gray-400 mt-1">Total memories</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-3xl font-bold text-blue-400">{byType.semantic}</p>
          <p className="text-xs text-gray-400 mt-1">Facts (semantic)</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-3xl font-bold text-purple-400">
            {byType.procedural}
          </p>
          <p className="text-xs text-gray-400 mt-1">Preferences (procedural)</p>
        </div>
      </div>

      <div className="flex gap-4">
        <Link
          href="/memories"
          className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-md text-sm hover:bg-gray-700"
        >
          Browse Memories
        </Link>
        <Link
          href="/conversations"
          className="px-4 py-2 bg-blue-600 rounded-md text-sm text-white hover:bg-blue-500"
        >
          Start Chatting
        </Link>
      </div>
    </div>
  );
}
