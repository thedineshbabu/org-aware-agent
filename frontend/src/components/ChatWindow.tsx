import { useEffect, useRef } from "react";
import type { ChatMessage } from "../hooks/useChat";
import MessageBubble from "./MessageBubble";

interface Props {
  messages: ChatMessage[];
  isLoading: boolean;
}

export default function ChatWindow({ messages, isLoading }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center text-gray-500 max-w-md">
          <p className="text-lg font-medium text-gray-700 mb-2">How can I help you today?</p>
          <p className="text-sm">
            Ask about internal policies, search documentation, query project data, or create Jira tickets.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      className="flex-1 overflow-y-auto p-4 space-y-4"
      role="log"
      aria-label="Conversation history"
      aria-live="polite"
    >
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}

      {isLoading && (
        <div className="flex items-center gap-2 text-gray-500 text-sm" aria-label="Agent is thinking">
          <div className="flex gap-1">
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
          </div>
          <span>Thinking…</span>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
