"use client";

import { useEffect, useState } from "react";
import { fetchMemories, fetchHealth } from "@/lib/api";
import type { Memory, HealthStatus } from "@/lib/types";
import HealthBadge from "@/components/HealthBadge";
import Link from "next/link";
import { BarChart3, Database, Cog, Clock, Brain, MessageSquare, AlertTriangle, ArrowRight } from "lucide-react";

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
    <div className="max-w-5xl">
      {/* Hero Section */}
      <div className="mb-10">
        <h2 className="text-3xl font-bold text-white mb-2">
          Your Memory Dashboard
        </h2>
        <p className="text-[#a3a3a3] text-sm">
          Monitor, explore, and manage your neural memory system
        </p>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-[#262626] border border-red-500/30 rounded-xl p-4 mb-8">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
            <div>
              <p className="text-sm text-red-400">{error}</p>
              <p className="text-xs text-[#a3a3a3] mt-0.5">
                Start the backend with{" "}
                <code className="bg-[#333] px-1.5 py-0.5 rounded text-[#e5e5e5] font-mono text-[11px]">
                  uvicorn backend.main:app --port 8001
                </code>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Health Badges Inline */}
      {health && (
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <h3 className="text-xs font-medium text-[#a3a3a3] uppercase tracking-wider">
              Services
            </h3>
            <span className="text-[10px] text-[#a3a3a3] bg-[#2a2a2a] border border-[#404040] px-2 py-0.5 rounded-full">
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

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
        {/* Total */}
        <div className="bg-[#262626] border border-[#333] rounded-xl p-5">
          <div className="flex items-start justify-between mb-3">
            <BarChart3 className="w-5 h-5 text-blue-400" />
            <span className="text-[10px] text-[#a3a3a3] bg-[#2a2a2a] border border-[#404040] px-2 py-0.5 rounded-full">total</span>
          </div>
          <p className="text-3xl font-bold text-blue-400">
            {memories.length}
          </p>
          <p className="text-xs text-[#a3a3a3] mt-1">Total memories</p>
        </div>

        {/* Semantic */}
        <div className="bg-[#262626] border border-[#333] rounded-xl p-5">
          <div className="flex items-start justify-between mb-3">
            <Database className="w-5 h-5 text-cyan-400" />
            <span className="text-[10px] text-[#a3a3a3] bg-[#2a2a2a] border border-[#404040] px-2 py-0.5 rounded-full">semantic</span>
          </div>
          <p className="text-3xl font-bold text-cyan-400">
            {byType.semantic}
          </p>
          <p className="text-xs text-[#a3a3a3] mt-1">Facts & knowledge</p>
        </div>

        {/* Procedural */}
        <div className="bg-[#262626] border border-[#333] rounded-xl p-5">
          <div className="flex items-start justify-between mb-3">
            <Cog className="w-5 h-5 text-purple-400" />
            <span className="text-[10px] text-[#a3a3a3] bg-[#2a2a2a] border border-[#404040] px-2 py-0.5 rounded-full">procedural</span>
          </div>
          <p className="text-3xl font-bold text-purple-400">
            {byType.procedural}
          </p>
          <p className="text-xs text-[#a3a3a3] mt-1">Preferences & habits</p>
        </div>

        {/* Episodic */}
        <div className="bg-[#262626] border border-[#333] rounded-xl p-5">
          <div className="flex items-start justify-between mb-3">
            <Clock className="w-5 h-5 text-amber-400" />
            <span className="text-[10px] text-[#a3a3a3] bg-[#2a2a2a] border border-[#404040] px-2 py-0.5 rounded-full">episodic</span>
          </div>
          <p className="text-3xl font-bold text-amber-400">
            {byType.episodic}
          </p>
          <p className="text-xs text-[#a3a3a3] mt-1">Experiences & events</p>
        </div>
      </div>

      {/* CTA Buttons */}
      <div className="flex flex-col sm:flex-row gap-3">
        <Link
          href="/memories"
          className="bg-[#2a2a2a] border border-[#404040] rounded-xl px-6 py-3 text-sm font-medium text-[#e5e5e5] hover:bg-[#333] transition-colors flex items-center gap-2"
        >
          <Brain className="w-4 h-4" />
          <span>Browse Memories</span>
          <ArrowRight className="w-3.5 h-3.5 text-[#666] ml-1" />
        </Link>
        <Link
          href="/conversations"
          className="bg-blue-600 hover:bg-blue-500 rounded-xl px-6 py-3 text-sm font-medium text-white transition-colors flex items-center gap-2"
        >
          <MessageSquare className="w-4 h-4" />
          <span>Start Chatting</span>
          <ArrowRight className="w-3.5 h-3.5 ml-1" />
        </Link>
      </div>
    </div>
  );
}
