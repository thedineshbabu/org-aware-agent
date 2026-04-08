import { useCallback, useState } from "react";
import { useAuth } from "react-oidc-context";
import api from "../lib/api";
import type { Citation } from "../components/CitationCard";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  requiresConfirmation?: boolean;
  pendingTicket?: Record<string, unknown> | null;
}

interface ChatApiResponse {
  session_id: string;
  message_id: string;
  content: string;
  citations: Citation[];
  requires_confirmation: boolean;
  pending_ticket: Record<string, unknown> | null;
  latency_ms: number;
}

export function useChat() {
  const auth = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!auth.user?.access_token) return;

      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: text,
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setError(null);

      try {
        const response = await api.post<ChatApiResponse>(
          "/api/v1/chat",
          { message: text, session_id: sessionId },
          { headers: { Authorization: `Bearer ${auth.user.access_token}` } }
        );

        const data = response.data;

        if (!sessionId) {
          setSessionId(data.session_id);
        }

        const assistantMessage: ChatMessage = {
          id: data.message_id,
          role: "assistant",
          content: data.content,
          citations: data.citations,
          requiresConfirmation: data.requires_confirmation,
          pendingTicket: data.pending_ticket,
        };

        setMessages((prev) => [...prev, assistantMessage]);
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "Something went wrong. Please try again.";
        setError(message);
        const errorMessage: ChatMessage = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `I encountered an error: ${message}`,
        };
        setMessages((prev) => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
      }
    },
    [auth.user?.access_token, sessionId]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    setSessionId(undefined);
    setError(null);
  }, []);

  return { messages, sendMessage, clearMessages, isLoading, error, sessionId };
}
