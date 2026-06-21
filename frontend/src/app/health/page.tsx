"use client";

import { useEffect, useState } from "react";
import { fetchHealth } from "@/lib/api";
import type { HealthStatus } from "@/lib/types";
import HealthBadge from "@/components/HealthBadge";

export default function HealthPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = () =>
      fetchHealth()
        .then(setHealth)
        .catch(() => setError("Cannot reach backend"));
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="max-w-2xl animate-fade-in">
      <div className="mb-8">
        <h2 className="text-2xl font-bold">
          <span className="gradient-text">System Health</span>
        </h2>
        <p className="text-xs text-gray-500 mt-1">
          Real-time service monitoring
        </p>
      </div>

      {/* ── Error Banner ─────────────────────────────── */}
      {error && (
        <div className="glass rounded-xl p-4 mb-6 border-red-500/20">
          <div className="flex items-center gap-3">
            <span className="text-red-400 text-lg">⚠️</span>
            <p className="text-sm text-red-300">{error}</p>
          </div>
        </div>
      )}

      {health && (
        <div className="space-y-6">
          {/* ── Status Overview ───────────────────────── */}
          <div className="glass rounded-xl p-6 animate-slide-up">
            <div className="flex items-center gap-4 mb-4">
              {/* Pulsing status indicator */}
              <span className="relative flex h-4 w-4">
                <span
                  className={`absolute inset-0 rounded-full animate-ping opacity-30 ${
                    health.status === "ok" ? "bg-green-400" : "bg-red-400"
                  }`}
                />
                <span
                  className={`relative inline-flex rounded-full h-4 w-4 ${
                    health.status === "ok" ? "bg-green-400" : "bg-red-400"
                  }`}
                />
              </span>
              <span className="text-lg font-semibold text-white">
                {health.status === "ok"
                  ? "All Systems Operational"
                  : "Degraded Performance"}
              </span>
            </div>
            <div className="flex gap-3 text-xs text-gray-500">
              <span className="glass px-2.5 py-1 rounded-lg">
                Version: {health.version}
              </span>
              <span className="glass px-2.5 py-1 rounded-lg">
                Env: {health.env}
              </span>
            </div>
          </div>

          {/* ── Services List ────────────────────────── */}
          <div className="animate-slide-up" style={{ animationDelay: "0.1s" }}>
            <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">
              Services
            </h3>
            <div className="flex flex-col gap-2">
              {Object.entries(health.services).map(([name, status]) => (
                <HealthBadge key={name} name={name} status={status} />
              ))}
            </div>
          </div>

          {/* ── Footer ───────────────────────────────── */}
          <p className="text-[11px] text-gray-600 flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400/40 animate-pulse-glow" />
            Auto-refreshing every 5 seconds
          </p>
        </div>
      )}
    </div>
  );
}
