import ChatInterface from "@/components/ChatInterface";

export default function ConversationsPage() {
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white">
          Chat with Memory
        </h2>
        <p className="text-xs text-[#a3a3a3] mt-1">
          Your conversation is remembered across sessions
        </p>
      </div>
      <ChatInterface />
    </div>
  );
}
