"use client";

import { useState, useRef, useEffect } from "react";
import { sendMessage } from "@/lib/api";
import type { ConversationResponse } from "@/lib/types";

/* ── localStorage persistence (DO NOT MODIFY) ─────────── */
const STORAGE_KEY = "chat-memory-messages";
const CONV_ID_KEY = "chat-memory-conv-id";

function loadMessages(): Message[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveMessages(msgs: Message[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(msgs));
  } catch {}
}
/* ── end persistence ───────────────────────────────────── */

interface Message {
  role: "user" | "assistant";
  content: string;
  memoriesUsed?: Array<Record<string, unknown>>;
  memoriesStored?: number;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>(loadMessages);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(() => {
    if (typeof window === "undefined") return "";
    return localStorage.getItem(CONV_ID_KEY) || "";
  });
  const bottomRef = useRef<HTMLDivElement>(null);

  /* ── Persist state (DO NOT MODIFY) ─────────────────── */
  useEffect(() => {
    saveMessages(messages);
  }, [messages]);

  useEffect(() => {
    if (conversationId) localStorage.setItem(CONV_ID_KEY, conversationId);
  }, [conversationId]);
  /* ── end persist ───────────────────────────────────── */

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);

    try {
      const resp: ConversationResponse = await sendMessage(
        userMsg,
        conversationId
      );
      if (!conversationId) setConversationId(resp.conversation_id);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: resp.response,
          memoriesUsed: resp.memories_used,
          memoriesStored: resp.memories_stored,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Error: could not reach the server." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] max-w-3xl mx-auto">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto space-y-4 pb-4 pr-2">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <span className="text-5xl mb-4">🧠</span>
            <p className="text-[#666] text-sm">
              Send a message to start a conversation with memory.
            </p>
            <p className="text-[#666] text-xs mt-1">
              Your chat history persists across sessions
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-[#262626] border border-[#333] text-[#e5e5e5]"
              }`}
            >
              <p className="text-sm whitespace-pre-wrap leading-relaxed">
                {msg.content}
              </p>
              {msg.role === "assistant" &&
                msg.memoriesUsed &&
                msg.memoriesUsed.length > 0 && (
                  <div className="mt-2.5 pt-2 border-t border-[#404040]">
                    <span className="inline-flex items-center gap-1.5 text-[11px] text-[#a3a3a3] bg-[#2a2a2a] px-2.5 py-1 rounded-full">
                      <span className="text-xs">🧠</span>
                      Memories used: {msg.memoriesUsed.length} | Stored:{" "}
                      {msg.memoriesStored ?? 0}
                    </span>
                  </div>
                )}
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-[#262626] border border-[#333] rounded-2xl px-5 py-3">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[#a3a3a3] animate-pulse" />
                <span className="w-2 h-2 rounded-full bg-[#a3a3a3] animate-pulse" style={{ animationDelay: "0.2s" }} />
                <span className="w-2 h-2 rounded-full bg-[#a3a3a3] animate-pulse" style={{ animationDelay: "0.4s" }} />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input Area */}
      <div className="pt-4 border-t border-[#333]">
        {/* Clear chat */}
        {messages.length > 0 && (
          <button
            onClick={() => {
              setMessages([]);
              setConversationId("");
              localStorage.removeItem(STORAGE_KEY);
              localStorage.removeItem(CONV_ID_KEY);
            }}
            className="mb-3 px-3 py-1 text-[11px] text-[#666] hover:text-[#999] transition-colors"
          >
            Clear Chat
          </button>
        )}

        <div className="flex gap-3">
          <div className="flex-1 relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Send a message..."
              className="w-full bg-[#2a2a2a] border border-[#404040] rounded-xl px-4 py-3 text-sm text-white placeholder-[#666] focus:outline-none focus:border-blue-500 transition-colors"
              disabled={loading}
            />
          </div>
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="px-5 py-3 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-xl disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
