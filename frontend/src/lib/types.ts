export interface Memory {
  id: string;
  user_id: string;
  type: "episodic" | "semantic" | "procedural";
  content: string;
  importance: number;
  confidence: number;
  weight: number;
  reinforcement_count: number;
  archived: boolean;
  source: Record<string, unknown>;
  created_at: string | null;
  updated_at: string | null;
}

export interface ScoredMemory {
  memory: Memory;
  final_score: number;
  score_breakdown: Record<string, number | string>;
}

export interface ConversationResponse {
  response: string;
  conversation_id: string;
  memories_used: Array<Record<string, unknown>>;
  memories_stored: number;
}

export interface HealthStatus {
  status: "ok" | "degraded";
  version: string;
  env: string;
  services: Record<string, string>;
}
