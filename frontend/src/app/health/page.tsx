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
    <div className="max-w-2xl">
      <h2 className="text-2xl font-bold mb-6">System Health</h2>

      {error && (
        <div className="bg-red-900/30 border border-red-800 rounded-md p-3 mb-4 text-sm text-red-300">
          {error}
        </div>
      )}

      {health && (
        <div className="space-y-6">
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="flex items-center gap-3 mb-4">
              <span
                className={`w-3 h-3 rounded-full ${
                  health.status === "ok" ? "bg-green-400" : "bg-red-400"
                }`}
              />
              <span className="text-lg font-semibold">
                {health.status === "ok" ? "All Systems Operational" : "Degraded"}
              </span>
            </div>
            <div className="flex gap-2 text-xs text-gray-400">
              <span>Version: {health.version}</span>
              <span>Env: {health.env}</span>
            </div>
          </div>

          <div>
            <h3 className="text-sm text-gray-400 mb-3">Services</h3>
            <div className="flex flex-col gap-2">
              {Object.entries(health.services).map(([name, status]) => (
                <HealthBadge key={name} name={name} status={status} />
              ))}
            </div>
          </div>

          <p className="text-xs text-gray-600">
            Auto-refreshing every 5 seconds
          </p>
        </div>
      )}
    </div>
  );
}
