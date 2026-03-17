"use client";

import { useState, useRef, useEffect } from "react";
import { askQuestion, ChatResponse } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: ChatResponse["sources"];
}

interface Props {
  documentId: string | null;
  documentName?: string;
}

export default function ChatBox({ documentId, documentName }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send() {
    const q = input.trim();
    if (!q || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setInput("");
    setLoading(true);

    try {
      const res = await askQuestion(q, documentId ?? undefined);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.answer, sources: res.sources },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Something went wrong. Is Ollama running?" },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="text-xs text-gray-400 px-4 pt-3 pb-1">
        {documentName
          ? `Asking: ${documentName}`
          : "Asking across all documents"}
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-2 space-y-4">
        {messages.length === 0 && (
          <p className="text-sm text-gray-400 mt-8 text-center">
            Ask something about your documents
          </p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className="max-w-[80%]">
              <div
                className={`rounded-xl px-4 py-2 text-sm whitespace-pre-wrap ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-800"
                }`}
              >
                {msg.content}
              </div>
              {msg.sources && msg.sources.length > 0 && (
                <details className="mt-1 text-xs text-gray-400">
                  <summary className="cursor-pointer hover:text-gray-600">
                    {msg.sources.length} source{msg.sources.length > 1 ? "s" : ""}
                  </summary>
                  <div className="mt-1 space-y-1">
                    {msg.sources.map((s, j) => (
                      <div key={j} className="bg-gray-50 border rounded p-2 text-gray-500">
                        <span className="font-medium text-gray-600">{s.filename}</span>
                        <p className="mt-0.5 line-clamp-2">{s.chunk}</p>
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-xl px-4 py-2 text-sm text-gray-400">
              Thinking...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t px-4 py-3 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
          placeholder="Ask a question..."
          className="flex-1 text-sm border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
        <button
          onClick={send}
          disabled={loading || !input.trim()}
          className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg disabled:opacity-40 hover:bg-blue-700 transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  );
}
