"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { fetchMemory } from "@/lib/api";
import type { Memory } from "@/lib/types";
import MemoryEditor from "@/components/MemoryEditor";

const TYPE_COLORS: Record<string, string> = {
  semantic: "text-blue-400",
  procedural: "text-purple-400",
  episodic: "text-amber-400",
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
      <div className="max-w-2xl">
        <div className="bg-[#262626] border border-[#333] rounded-xl p-6 text-center">
          <span className="text-4xl block mb-3">😵</span>
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
      <div className="flex items-center justify-center py-20">
        <p className="text-[#a3a3a3] text-sm">Loading...</p>
      </div>
    );

  return (
    <div className="max-w-2xl">
      {/* Back Button */}
      <button
        onClick={() => router.push("/memories")}
        className="text-sm text-[#a3a3a3] hover:text-white mb-6 inline-flex items-center gap-1 transition-colors"
      >
        <span>&larr;</span>
        <span>Back to memories</span>
      </button>

      <h2 className="text-xl font-bold text-white mb-6">
        Memory Detail
      </h2>

      {/* Detail Card */}
      <div className="bg-[#262626] border border-[#333] rounded-xl p-5 mb-8 space-y-3 text-sm">
        <DetailRow label="ID">
          <span className="font-mono text-[11px] text-[#e5e5e5] bg-[#333] px-2 py-0.5 rounded">
            {memory.id}
          </span>
        </DetailRow>
        <DetailRow label="Type">
          <span className={`font-medium ${TYPE_COLORS[memory.type] || "text-[#e5e5e5]"}`}>
            {memory.type}
          </span>
        </DetailRow>
        <DetailRow label="Weight">
          <span className="text-[#e5e5e5]">{memory.weight.toFixed(4)}</span>
        </DetailRow>
        <DetailRow label="Reinforced">
          <span className="text-[#e5e5e5]">{memory.reinforcement_count} times</span>
        </DetailRow>
        <DetailRow label="Source">
          <span className="font-mono text-[11px] text-[#a3a3a3] bg-[#333] px-2 py-0.5 rounded">
            {JSON.stringify(memory.source)}
          </span>
        </DetailRow>
        {memory.created_at && (
          <DetailRow label="Created">
            <span className="text-[#e5e5e5]">
              {new Date(memory.created_at).toLocaleString()}
            </span>
          </DetailRow>
        )}
      </div>

      {/* Editor */}
      <div>
        <h3 className="text-xs font-medium text-[#a3a3a3] uppercase tracking-wider mb-4">
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
      <span className="text-[#a3a3a3] min-w-[80px] text-xs font-medium uppercase tracking-wider pt-0.5">
        {label}
      </span>
      <div className="flex-1">{children}</div>
    </div>
  );
}
