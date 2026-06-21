"use client";

import { useState, useRef, useEffect } from "react";
import { sendMessage } from "@/lib/api";
import type { ConversationResponse } from "@/lib/types";

interface Message {
  role: "user" | "assistant";
  content: string;
  memoriesUsed?: Array<Record<string, unknown>>;
  memoriesStored?: number;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

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
    <div className="flex flex-col h-[calc(100vh-3rem)] max-w-3xl mx-auto">
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.length === 0 && (
          <p className="text-gray-500 text-center mt-20">
            Send a message to start a conversation with memory.
          </p>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-800 text-gray-200"
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              {msg.role === "assistant" && msg.memoriesUsed && msg.memoriesUsed.length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-700">
                  <p className="text-xs text-gray-400">
                    Memories used: {msg.memoriesUsed.length} | Stored: {msg.memoriesStored ?? 0}
                  </p>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-800 rounded-lg px-4 py-2 text-sm text-gray-400">
              Thinking...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-gray-800 pt-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Send a message..."
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
