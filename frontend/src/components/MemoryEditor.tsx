"use client";

import { useState } from "react";
import { updateMemory, deleteMemory } from "@/lib/api";
import type { Memory } from "@/lib/types";

export default function MemoryEditor({
  memory,
  onUpdate,
}: {
  memory: Memory;
  onUpdate: () => void;
}) {
  const [content, setContent] = useState(memory.content);
  const [importance, setImportance] = useState(memory.importance);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function handleSave() {
    setSaving(true);
    try {
      await updateMemory(memory.id, { content, importance });
      onUpdate();
    } catch (err) {
      alert("Failed to save");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirm("Delete this memory? It will no longer appear in retrieval."))
      return;
    setDeleting(true);
    try {
      await deleteMemory(memory.id);
      onUpdate();
    } catch (err) {
      alert("Failed to delete");
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="space-y-5">
      {/* ── Content textarea ─────────────────────────── */}
      <div>
        <label className="block text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-2">
          Content
        </label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="w-full glass-input rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-blue-500/40 focus:shadow-[0_0_20px_rgba(59,130,246,0.1)] transition-all duration-300 resize-none"
          rows={3}
        />
      </div>

      {/* ── Importance slider ────────────────────────── */}
      <div>
        <label className="block text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-2">
          Importance
          <span className="ml-2 text-blue-400 normal-case">
            {importance}/10
          </span>
        </label>
        <div className="relative">
          <input
            type="range"
            min={1}
            max={10}
            value={importance}
            onChange={(e) => setImportance(Number(e.target.value))}
            className="w-full h-1.5 rounded-full appearance-none cursor-pointer bg-white/[0.06]
              [&::-webkit-slider-thumb]:appearance-none
              [&::-webkit-slider-thumb]:w-4
              [&::-webkit-slider-thumb]:h-4
              [&::-webkit-slider-thumb]:rounded-full
              [&::-webkit-slider-thumb]:bg-gradient-to-r
              [&::-webkit-slider-thumb]:from-blue-500
              [&::-webkit-slider-thumb]:to-purple-500
              [&::-webkit-slider-thumb]:shadow-[0_0_10px_rgba(59,130,246,0.3)]
              [&::-webkit-slider-thumb]:cursor-pointer
              [&::-webkit-slider-thumb]:border-0"
          />
        </div>
      </div>

      {/* ── Buttons ──────────────────────────────────── */}
      <div className="flex gap-3 pt-2">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white text-sm font-medium rounded-xl hover:from-blue-500 hover:to-purple-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-300 hover:shadow-[0_0_25px_rgba(59,130,246,0.3)]"
        >
          {saving ? "Saving..." : "Save Changes"}
        </button>
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="px-5 py-2.5 glass text-red-400 text-sm font-medium rounded-xl hover:bg-red-500/10 hover:text-red-300 hover:border-red-500/20 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-300"
        >
          {deleting ? "Deleting..." : "Delete Memory"}
        </button>
      </div>
    </div>
  );
}
