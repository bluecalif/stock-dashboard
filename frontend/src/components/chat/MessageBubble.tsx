import type { ChatMessage } from "../../types/chat";

interface Props {
  message: ChatMessage;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";
  const isAssistant = message.role === "assistant";

  if (message.role === "tool") {
    return (
      <div className="mx-4 my-1 text-xs text-gray-400 bg-gray-50 rounded px-3 py-1 font-mono truncate">
        🔧 Tool: {message.content?.slice(0, 100)}
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} px-4 py-1`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm whitespace-pre-wrap ${
          isUser
            ? "bg-blue-600 text-white rounded-br-md"
            : "bg-white text-gray-800 border border-gray-200 rounded-bl-md"
        }`}
      >
        {message.content || (isAssistant ? "..." : "")}
      </div>
    </div>
  );
}
