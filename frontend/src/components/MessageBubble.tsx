import type { ChatMessage } from "../hooks/useChat";
import CitationList from "./CitationList";

interface Props {
  message: ChatMessage;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[80%] ${isUser ? "items-end" : "items-start"} flex flex-col gap-2`}>
        {/* Message bubble */}
        <div
          className={`px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
            isUser
              ? "bg-brand-600 text-white rounded-br-sm"
              : "bg-white border border-gray-200 text-gray-800 rounded-bl-sm shadow-sm"
          }`}
          role={isUser ? undefined : "article"}
          aria-label={isUser ? "Your message" : "Agent response"}
        >
          {message.content}
        </div>

        {/* Confirmation prompt */}
        {message.requiresConfirmation && message.pendingTicket && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm w-full">
            <p className="font-medium text-amber-800 mb-1">Confirm Jira ticket creation:</p>
            <pre className="text-xs text-amber-700 whitespace-pre-wrap">
              {JSON.stringify(message.pendingTicket, null, 2)}
            </pre>
            <p className="text-amber-600 mt-2 text-xs">Reply "yes" to create, or describe changes.</p>
          </div>
        )}

        {/* Source citations */}
        {!isUser && message.citations && message.citations.length > 0 && (
          <CitationList citations={message.citations} />
        )}
      </div>
    </div>
  );
}
