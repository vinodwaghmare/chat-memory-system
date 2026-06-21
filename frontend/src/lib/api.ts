import type { Memory, ConversationResponse, HealthStatus } from "./types";

const API_HOST = process.env.NEXT_PUBLIC_BACKEND_URL || "";
const BASE = `${API_HOST}/api/v1`;
const DEFAULT_USER_ID = "demo-user-001";

function headers(userId?: string): HeadersInit {
  return {
    "Content-Type": "application/json",
    "X-User-ID": userId || DEFAULT_USER_ID,
  };
}

export async function fetchMemories(
  userId?: string,
  type?: string
): Promise<Memory[]> {
  const params = new URLSearchParams();
  if (type) params.set("type", type);
  const res = await fetch(`${BASE}/memories?${params}`, {
    headers: headers(userId),
  });
  if (!res.ok) throw new Error(`Failed to fetch memories: ${res.status}`);
  return res.json();
}

export async function fetchMemory(
  id: string,
  userId?: string
): Promise<Memory> {
  const res = await fetch(`${BASE}/memories/${id}`, {
    headers: headers(userId),
  });
  if (!res.ok) throw new Error(`Memory not found: ${res.status}`);
  return res.json();
}

export async function deleteMemory(
  id: string,
  userId?: string
): Promise<void> {
  const res = await fetch(`${BASE}/memories/${id}`, {
    method: "DELETE",
    headers: headers(userId),
  });
  if (!res.ok) throw new Error(`Delete failed: ${res.status}`);
}

export async function updateMemory(
  id: string,
  updates: Partial<Pick<Memory, "content" | "type" | "importance">>,
  userId?: string
): Promise<Memory> {
  const res = await fetch(`${BASE}/memories/${id}`, {
    method: "PUT",
    headers: headers(userId),
    body: JSON.stringify(updates),
  });
  if (!res.ok) throw new Error(`Update failed: ${res.status}`);
  return res.json();
}

export async function sendMessage(
  message: string,
  conversationId?: string,
  userId?: string
): Promise<ConversationResponse> {
  const res = await fetch(`${BASE}/conversations/message`, {
    method: "POST",
    headers: headers(userId),
    body: JSON.stringify({ message, conversation_id: conversationId || "" }),
  });
  if (!res.ok) throw new Error(`Message failed: ${res.status}`);
  return res.json();
}

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_HOST}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}
