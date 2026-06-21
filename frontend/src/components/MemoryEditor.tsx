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
    <div className="space-y-4">
      <div>
        <label className="block text-xs text-gray-400 mb-1">Content</label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
          rows={3}
        />
      </div>
      <div>
        <label className="block text-xs text-gray-400 mb-1">
          Importance ({importance}/10)
        </label>
        <input
          type="range"
          min={1}
          max={10}
          value={importance}
          onChange={(e) => setImportance(Number(e.target.value))}
          className="w-full"
        />
      </div>
      <div className="flex gap-2">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-500 disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save Changes"}
        </button>
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="px-4 py-2 bg-red-700 text-white text-sm rounded-md hover:bg-red-600 disabled:opacity-50"
        >
          {deleting ? "Deleting..." : "Delete Memory"}
        </button>
      </div>
    </div>
  );
}
