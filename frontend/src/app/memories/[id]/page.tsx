"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { fetchMemory } from "@/lib/api";
import type { Memory } from "@/lib/types";
import MemoryEditor from "@/components/MemoryEditor";

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
        <p className="text-red-400">{error}</p>
        <button
          onClick={() => router.push("/memories")}
          className="mt-4 text-sm text-blue-400 hover:underline"
        >
          Back to memories
        </button>
      </div>
    );
  }

  if (!memory) return <p className="text-gray-500 text-sm">Loading...</p>;

  return (
    <div className="max-w-2xl">
      <button
        onClick={() => router.push("/memories")}
        className="text-sm text-gray-400 hover:text-white mb-4 inline-block"
      >
        &larr; Back to memories
      </button>

      <h2 className="text-xl font-bold mb-4">Memory Detail</h2>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 mb-6 space-y-2 text-sm">
        <div className="flex gap-4">
          <span className="text-gray-400">ID:</span>
          <span className="text-gray-200 font-mono text-xs">{memory.id}</span>
        </div>
        <div className="flex gap-4">
          <span className="text-gray-400">Type:</span>
          <span className="text-gray-200">{memory.type}</span>
        </div>
        <div className="flex gap-4">
          <span className="text-gray-400">Weight:</span>
          <span className="text-gray-200">{memory.weight.toFixed(4)}</span>
        </div>
        <div className="flex gap-4">
          <span className="text-gray-400">Reinforced:</span>
          <span className="text-gray-200">
            {memory.reinforcement_count} times
          </span>
        </div>
        <div className="flex gap-4">
          <span className="text-gray-400">Source:</span>
          <span className="text-gray-200 font-mono text-xs">
            {JSON.stringify(memory.source)}
          </span>
        </div>
        {memory.created_at && (
          <div className="flex gap-4">
            <span className="text-gray-400">Created:</span>
            <span className="text-gray-200">
              {new Date(memory.created_at).toLocaleString()}
            </span>
          </div>
        )}
      </div>

      <h3 className="text-sm text-gray-400 mb-3">Edit / Correct</h3>
      <MemoryEditor memory={memory} onUpdate={handleUpdate} />
    </div>
  );
}
