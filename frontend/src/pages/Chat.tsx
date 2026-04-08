import { useAuth } from "react-oidc-context";
import ChatWindow from "../components/ChatWindow";
import MessageInput from "../components/MessageInput";
import { useChat } from "../hooks/useChat";

export default function Chat() {
  const auth = useAuth();
  const { messages, sendMessage, isLoading } = useChat();

  const user = auth.user?.profile;
  const displayName = user?.name || user?.preferred_username || "User";

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold text-gray-900">Org AI Agent</h1>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600" aria-label="Signed in as">
            {displayName}
          </span>
          <button
            onClick={() => auth.signoutRedirect()}
            className="text-sm text-gray-500 hover:text-gray-700 underline"
            aria-label="Sign out"
          >
            Sign out
          </button>
        </div>
      </header>

      {/* Chat area */}
      <main className="flex-1 flex flex-col overflow-hidden max-w-4xl w-full mx-auto">
        <ChatWindow messages={messages} isLoading={isLoading} />
        <MessageInput onSend={sendMessage} isLoading={isLoading} />
      </main>
    </div>
  );
}
