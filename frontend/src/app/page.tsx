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
    <div className="max-w-5xl animate-fade-in">
      {/* ── Hero Section ─────────────────────────────── */}
      <div className="mb-10">
        <h2 className="text-3xl font-bold mb-2">
          <span className="gradient-text">Your Memory Dashboard</span>
        </h2>
        <p className="text-gray-500 text-sm">
          Monitor, explore, and manage your neural memory system
        </p>
      </div>

      {/* ── Error Banner ─────────────────────────────── */}
      {error && (
        <div className="glass rounded-xl p-4 mb-8 border-red-500/20 animate-fade-in">
          <div className="flex items-center gap-3">
            <span className="text-red-400 text-lg">⚠️</span>
            <div>
              <p className="text-sm text-red-300">{error}</p>
              <p className="text-xs text-gray-500 mt-0.5">
                Start the backend with{" "}
                <code className="bg-white/[0.06] px-1.5 py-0.5 rounded text-gray-300 font-mono text-[11px]">
                  uvicorn backend.main:app --port 8001
                </code>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ── Health Badges Inline ──────────────────────── */}
      {health && (
        <div className="mb-8 animate-fade-in">
          <div className="flex items-center gap-3 mb-3">
            <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider">
              Services
            </h3>
            <span className="text-[10px] text-gray-600 glass px-2 py-0.5 rounded-full">
              v{health.version}
            </span>
          </div>
          <div className="flex gap-2 flex-wrap">
            {Object.entries(health.services).map(([name, status]) => (
              <HealthBadge key={name} name={name} status={status} />
            ))}
          </div>
        </div>
      )}

      {/* ── Stat Cards ───────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
        {/* Total */}
        <div className="glass rounded-xl p-5 hover:glow-blue transition-all duration-300 group animate-slide-up">
          <div className="flex items-start justify-between mb-3">
            <span className="text-2xl">📊</span>
            <span className="text-[10px] text-gray-500 glass px-2 py-0.5 rounded-full">total</span>
          </div>
          <p className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-blue-300 bg-clip-text text-transparent">
            {memories.length}
          </p>
          <p className="text-xs text-gray-500 mt-1">Total memories</p>
        </div>

        {/* Semantic */}
        <div className="glass rounded-xl p-5 hover:glow-cyan transition-all duration-300 group animate-slide-up" style={{ animationDelay: "0.05s" }}>
          <div className="flex items-start justify-between mb-3">
            <span className="text-2xl">🔵</span>
            <span className="text-[10px] text-gray-500 glass px-2 py-0.5 rounded-full">semantic</span>
          </div>
          <p className="text-3xl font-bold gradient-text-cyan">
            {byType.semantic}
          </p>
          <p className="text-xs text-gray-500 mt-1">Facts & knowledge</p>
        </div>

        {/* Procedural */}
        <div className="glass rounded-xl p-5 hover:glow-purple transition-all duration-300 group animate-slide-up" style={{ animationDelay: "0.1s" }}>
          <div className="flex items-start justify-between mb-3">
            <span className="text-2xl">🟣</span>
            <span className="text-[10px] text-gray-500 glass px-2 py-0.5 rounded-full">procedural</span>
          </div>
          <p className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            {byType.procedural}
          </p>
          <p className="text-xs text-gray-500 mt-1">Preferences & habits</p>
        </div>

        {/* Episodic */}
        <div className="glass rounded-xl p-5 hover:glow-amber transition-all duration-300 group animate-slide-up" style={{ animationDelay: "0.15s" }}>
          <div className="flex items-start justify-between mb-3">
            <span className="text-2xl">🟡</span>
            <span className="text-[10px] text-gray-500 glass px-2 py-0.5 rounded-full">episodic</span>
          </div>
          <p className="text-3xl font-bold bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">
            {byType.episodic}
          </p>
          <p className="text-xs text-gray-500 mt-1">Experiences & events</p>
        </div>
      </div>

      {/* ── CTA Buttons ──────────────────────────────── */}
      <div className="flex gap-4 animate-fade-in">
        <Link
          href="/memories"
          className="group glass rounded-xl px-6 py-3 text-sm font-medium text-gray-300 hover:text-white hover:bg-white/[0.06] transition-all duration-300 flex items-center gap-2"
        >
          <span>🧠</span>
          <span>Browse Memories</span>
          <span className="text-gray-600 group-hover:text-gray-400 transition-colors ml-1">&rarr;</span>
        </Link>
        <Link
          href="/conversations"
          className="group relative rounded-xl px-6 py-3 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 transition-all duration-300 flex items-center gap-2 hover:shadow-[0_0_30px_rgba(59,130,246,0.3)]"
        >
          <span>💬</span>
          <span>Start Chatting</span>
          <span className="ml-1 group-hover:translate-x-0.5 transition-transform">&rarr;</span>
        </Link>
      </div>
    </div>
  );
}
