"use client";

import { useEffect, useState } from "react";
import { fetchHealth } from "@/lib/api";
import type { HealthStatus } from "@/lib/types";
import { Activity } from "lucide-react";
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
    <div className="max-w-2xl">
      <div className="mb-8 flex items-center gap-3">
        <Activity className="w-6 h-6 text-blue-400" />
        <h2 className="text-2xl font-bold text-white">
          System Health
        </h2>
        <p className="text-xs text-[#a3a3a3] mt-1">
          Real-time service monitoring
        </p>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-[#262626] border border-red-500/30 rounded-xl p-4 mb-6">
          <div className="flex items-center gap-3">
            <span className="text-red-400 text-lg">⚠️</span>
            <p className="text-sm text-red-400">{error}</p>
          </div>
        </div>
      )}

      {health && (
        <div className="space-y-6">
          {/* Status Overview */}
          <div className="bg-[#262626] border border-[#333] rounded-xl p-6">
            <div className="flex items-center gap-4 mb-4">
              {/* Status dot */}
              <span
                className={`w-4 h-4 rounded-full ${
                  health.status === "ok" ? "bg-green-400" : "bg-red-400"
                }`}
              />
              <span className="text-lg font-semibold text-white">
                {health.status === "ok"
                  ? "All Systems Operational"
                  : "Degraded Performance"}
              </span>
            </div>
            <div className="flex gap-3 text-xs text-[#a3a3a3]">
              <span className="bg-[#2a2a2a] border border-[#404040] px-2.5 py-1 rounded-lg">
                Version: {health.version}
              </span>
              <span className="bg-[#2a2a2a] border border-[#404040] px-2.5 py-1 rounded-lg">
                Env: {health.env}
              </span>
            </div>
          </div>

          {/* Services List */}
          <div>
            <h3 className="text-xs font-medium text-[#a3a3a3] uppercase tracking-wider mb-3">
              Services
            </h3>
            <div className="flex flex-col gap-2">
              {Object.entries(health.services).map(([name, status]) => (
                <HealthBadge key={name} name={name} status={status} />
              ))}
            </div>
          </div>

          {/* Footer */}
          <p className="text-[11px] text-[#666] flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
            Auto-refreshing every 5 seconds
          </p>
        </div>
      )}
    </div>
  );
}
