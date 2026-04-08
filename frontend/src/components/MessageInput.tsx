import { FormEvent, KeyboardEvent, useRef, useState } from "react";

interface Props {
  onSend: (message: string) => void;
  isLoading: boolean;
}

export default function MessageInput({ onSend, isLoading }: Props) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e?: FormEvent) => {
    e?.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    setValue("");
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="border-t border-gray-200 bg-white px-4 py-3"
      aria-label="Message input"
    >
      <div className="flex items-end gap-3 max-w-4xl mx-auto">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder="Ask a question or describe a task… (Enter to send, Shift+Enter for new line)"
          disabled={isLoading}
          rows={1}
          className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-2.5 text-sm
                     focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent
                     disabled:opacity-50 disabled:bg-gray-50 max-h-48 overflow-y-auto"
          aria-label="Type your message"
          aria-multiline="true"
        />
        <button
          type="submit"
          disabled={isLoading || !value.trim()}
          className="shrink-0 rounded-xl bg-brand-600 hover:bg-brand-700 text-white px-4 py-2.5
                     text-sm font-medium transition-colors focus:outline-none focus:ring-2
                     focus:ring-brand-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Send message"
        >
          {isLoading ? "…" : "Send"}
        </button>
      </div>
      <p className="text-xs text-gray-400 text-center mt-1">
        Responses are grounded in your organization's internal data.
      </p>
    </form>
  );
}
