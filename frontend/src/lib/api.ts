import type { Memory, ConversationResponse, HealthStatus } from "./types";

const API_HOST = process.env.NEXT_PUBLIC_BACKEND_URL || "";
const BASE = `${API_HOST}/api/v1`;

const ACCESS_TOKEN_KEY = "chat-memory-access-token";
const REFRESH_TOKEN_KEY = "chat-memory-refresh-token";

function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

function authHeaders(): HeadersInit {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  const token = getAccessToken();
  if (token) h["Authorization"] = `Bearer ${token}`;
  return h;
}

export function isLoggedIn(): boolean {
  if (typeof window === "undefined") return false;
  return !!localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function logout(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem("chat-memory-messages");
  localStorage.removeItem("chat-memory-conv-id");
}

export interface AuthUser {
  user_id: string;
  email: string;
  name: string | null;
  picture: string | null;
}

export async function googleLogin(idToken: string): Promise<AuthUser> {
  const res = await fetch(`${BASE}/auth/google`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id_token: idToken }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Login failed: ${res.status}`);
  }
  const data = await res.json();
  localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
  return {
    user_id: data.user_id,
    email: data.email,
    name: data.name,
    picture: data.picture,
  };
}

async function tryRefresh(): Promise<boolean> {
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
  if (!refreshToken) return false;
  try {
    const res = await fetch(`${BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

async function authFetch(url: string, options: RequestInit = {}): Promise<Response> {
  options.headers = { ...authHeaders(), ...(options.headers || {}) };
  let res = await fetch(url, options);
  if (res.status === 401) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      options.headers = { ...authHeaders(), ...(options.headers || {}) };
      res = await fetch(url, options);
    }
  }
  return res;
}

export async function getUser(): Promise<AuthUser | null> {
  if (!isLoggedIn()) return null;
  try {
    const res = await authFetch(`${BASE}/auth/me`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function fetchMemories(type?: string): Promise<Memory[]> {
  const params = new URLSearchParams();
  if (type) params.set("type", type);
  const res = await authFetch(`${BASE}/memories?${params}`);
  if (!res.ok) throw new Error(`Failed to fetch memories: ${res.status}`);
  return res.json();
}

export async function fetchMemory(id: string): Promise<Memory> {
  const res = await authFetch(`${BASE}/memories/${id}`);
  if (!res.ok) throw new Error(`Memory not found: ${res.status}`);
  return res.json();
}

export async function deleteMemory(id: string): Promise<void> {
  const res = await authFetch(`${BASE}/memories/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Delete failed: ${res.status}`);
}

export async function updateMemory(
  id: string,
  updates: Partial<Pick<Memory, "content" | "type" | "importance">>,
): Promise<Memory> {
  const res = await authFetch(`${BASE}/memories/${id}`, {
    method: "PUT",
    body: JSON.stringify(updates),
  });
  if (!res.ok) throw new Error(`Update failed: ${res.status}`);
  return res.json();
}

export async function sendMessage(
  message: string,
  conversationId?: string,
): Promise<ConversationResponse> {
  const res = await authFetch(`${BASE}/conversations/message`, {
    method: "POST",
    body: JSON.stringify({ message, conversation_id: conversationId || "" }),
  });
  if (!res.ok) throw new Error(`Message failed: ${res.status}`);
  return res.json();
}

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_HOST}/health`);
  const data = await res.json();
  return data;
}
