"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { fetchMemory } from "@/lib/api";
import type { Memory } from "@/lib/types";
import MemoryEditor from "@/components/MemoryEditor";

const TYPE_COLORS: Record<string, string> = {
  semantic: "text-blue-300",
  procedural: "text-purple-300",
  episodic: "text-amber-300",
};

export default function MemoryDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [memory, setMemory] = useState<Memory | null>(null);
  const [error, setError] = useState("");

  const id = params.id as string;

  useEffect(() => {
    fetchMemory(id)
      .then(setMemory)
      .catch(() => setError("Memory not found"));
  }, [id]);

  function handleUpdate() {
    fetchMemory(id)
      .then(setMemory)
      .catch(() => router.push("/memories"));
  }

  if (error) {
    return (
      <div className="max-w-2xl animate-fade-in">
        <div className="glass rounded-xl p-6 text-center">
          <span className="text-4xl block mb-3 opacity-40">😵</span>
          <p className="text-red-400 text-sm">{error}</p>
          <button
            onClick={() => router.push("/memories")}
            className="mt-4 text-sm text-blue-400 hover:text-blue-300 transition-colors"
          >
            &larr; Back to memories
          </button>
        </div>
      </div>
    );
  }

  if (!memory)
    return (
      <div className="flex items-center gap-3 text-gray-500 py-20 justify-center">
        <span className="w-2 h-2 rounded-full bg-blue-400 animate-dot-bounce" />
        <span
          className="w-2 h-2 rounded-full bg-purple-400 animate-dot-bounce"
          style={{ animationDelay: "0.16s" }}
        />
        <span
          className="w-2 h-2 rounded-full bg-blue-400 animate-dot-bounce"
          style={{ animationDelay: "0.32s" }}
        />
      </div>
    );

  return (
    <div className="max-w-2xl animate-fade-in">
      {/* ── Back Button ──────────────────────────────── */}
      <button
        onClick={() => router.push("/memories")}
        className="text-sm text-gray-400 hover:text-white mb-6 inline-flex items-center gap-1 transition-colors group"
      >
        <span className="group-hover:-translate-x-0.5 transition-transform">&larr;</span>
        <span>Back to memories</span>
      </button>

      <h2 className="text-xl font-bold mb-6">
        <span className="gradient-text">Memory Detail</span>
      </h2>

      {/* ── Detail Card ──────────────────────────────── */}
      <div className="glass rounded-xl p-5 mb-8 space-y-3 text-sm animate-slide-up">
        <DetailRow label="ID">
          <span className="font-mono text-[11px] text-gray-300 bg-white/[0.04] px-2 py-0.5 rounded">
            {memory.id}
          </span>
        </DetailRow>
        <DetailRow label="Type">
          <span className={`font-medium ${TYPE_COLORS[memory.type] || "text-gray-300"}`}>
            {memory.type}
          </span>
        </DetailRow>
        <DetailRow label="Weight">
          <span className="text-gray-200">{memory.weight.toFixed(4)}</span>
        </DetailRow>
        <DetailRow label="Reinforced">
          <span className="text-gray-200">{memory.reinforcement_count} times</span>
        </DetailRow>
        <DetailRow label="Source">
          <span className="font-mono text-[11px] text-gray-400 bg-white/[0.04] px-2 py-0.5 rounded">
            {JSON.stringify(memory.source)}
          </span>
        </DetailRow>
        {memory.created_at && (
          <DetailRow label="Created">
            <span className="text-gray-200">
              {new Date(memory.created_at).toLocaleString()}
            </span>
          </DetailRow>
        )}
      </div>

      {/* ── Editor ───────────────────────────────────── */}
      <div className="animate-slide-up" style={{ animationDelay: "0.1s" }}>
        <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-4">
          Edit / Correct
        </h3>
        <MemoryEditor memory={memory} onUpdate={handleUpdate} />
      </div>
    </div>
  );
}

function DetailRow({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-4">
      <span className="text-gray-500 min-w-[80px] text-xs font-medium uppercase tracking-wider pt-0.5">
        {label}
      </span>
      <div className="flex-1">{children}</div>
    </div>
  );
}
