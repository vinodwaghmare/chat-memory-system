import ChatInterface from "@/components/ChatInterface";
import { MessageSquare } from "lucide-react";

export default function ConversationsPage() {
  return (
    <div>
      <div className="mb-6 flex items-center gap-3">
        <MessageSquare className="w-6 h-6 text-blue-400" />
        <div>
          <h2 className="text-2xl font-bold text-white">
            Chat with Memory
          </h2>
          <p className="text-xs text-[#a3a3a3] mt-0.5">
            Your conversation is remembered across sessions
          </p>
        </div>
      </div>
      <ChatInterface />
    </div>
  );
}
