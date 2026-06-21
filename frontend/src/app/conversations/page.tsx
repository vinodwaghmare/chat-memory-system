import ChatInterface from "@/components/ChatInterface";

export default function ConversationsPage() {
  return (
    <div className="animate-fade-in">
      <div className="mb-6">
        <h2 className="text-2xl font-bold">
          <span className="gradient-text">Chat with Memory</span>
        </h2>
        <p className="text-xs text-gray-500 mt-1">
          Your conversation is remembered across sessions
        </p>
      </div>
      <ChatInterface />
    </div>
  );
}
