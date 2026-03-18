"use client";

import { useState, useRef, useEffect } from "react";
import { askQuestion, ChatResponse } from "@/lib/api";
import { Send, ChevronDown, BookOpen, User } from "lucide-react";

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
  const [openSources, setOpenSources] = useState<number | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

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
        {
          role: "assistant",
          content: "Something went wrong — make sure Ollama is running and models are pulled.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div
        className="px-6 py-3 border-b flex items-center gap-2 shrink-0"
        style={{ borderColor: "var(--border)", background: "var(--surface)" }}
      >
        <div
          className="w-2 h-2 rounded-full"
          style={{ background: documentId ? "var(--accent)" : "#22c55e" }}
        />
        <span className="text-sm font-medium" style={{ color: "var(--text)" }}>
          {documentName ?? "All documents"}
        </span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center space-y-2">
              <p className="text-sm font-medium" style={{ color: "var(--text-muted)" }}>
                Ask anything about your document
              </p>
              <p className="text-xs" style={{ color: "var(--text-subtle)" }}>
                Press Enter to send · Shift+Enter for new line
              </p>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            {msg.role === "assistant" && (
              <div
                className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
                style={{ background: "var(--accent)" }}
              >
                <BookOpen size={13} color="white" />
              </div>
            )}

            <div className="max-w-[75%] space-y-2">
              <div
                className="rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap"
                style={
                  msg.role === "user"
                    ? { background: "var(--accent)", color: "white", borderBottomRightRadius: "4px" }
                    : { background: "var(--surface-2)", color: "var(--text)", borderBottomLeftRadius: "4px" }
                }
              >
                {msg.content}
              </div>

              {msg.sources && msg.sources.length > 0 && (
                <div>
                  <button
                    onClick={() => setOpenSources(openSources === i ? null : i)}
                    className="flex items-center gap-1.5 text-xs transition-colors"
                    style={{ color: "var(--text-subtle)" }}
                  >
                    <ChevronDown
                      size={12}
                      style={{ transform: openSources === i ? "rotate(180deg)" : "none", transition: "transform 0.2s" }}
                    />
                    {msg.sources.length} source{msg.sources.length > 1 ? "s" : ""}
                  </button>

                  {openSources === i && (
                    <div className="mt-2 space-y-2">
                      {msg.sources.map((s, j) => (
                        <div
                          key={j}
                          className="rounded-lg p-3 text-xs border"
                          style={{ background: "var(--surface-2)", borderColor: "var(--border)" }}
                        >
                          <p className="font-semibold mb-1" style={{ color: "var(--text-muted)" }}>
                            {s.filename}
                          </p>
                          <p
                            className="leading-relaxed line-clamp-3"
                            style={{ color: "var(--text-subtle)" }}
                          >
                            {s.chunk}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {msg.role === "user" && (
              <div
                className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
                style={{ background: "var(--surface-2)" }}
              >
                <User size={13} style={{ color: "var(--text-muted)" }} />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3 justify-start">
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
              style={{ background: "var(--accent)" }}
            >
              <BookOpen size={13} color="white" />
            </div>
            <div
              className="rounded-2xl px-4 py-3 flex items-center gap-1"
              style={{ background: "var(--surface-2)", borderBottomLeftRadius: "4px" }}
            >
              <span className="dot-1 w-1.5 h-1.5 rounded-full inline-block" style={{ background: "var(--text-subtle)" }} />
              <span className="dot-2 w-1.5 h-1.5 rounded-full inline-block" style={{ background: "var(--text-subtle)" }} />
              <span className="dot-3 w-1.5 h-1.5 rounded-full inline-block" style={{ background: "var(--text-subtle)" }} />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div
        className="px-6 py-4 border-t shrink-0"
        style={{ borderColor: "var(--border)", background: "var(--surface)" }}
      >
        <div
          className="flex items-end gap-3 rounded-xl border px-4 py-3 transition-colors"
          style={{ background: "var(--surface-2)", borderColor: "var(--border)" }}
        >
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask a question…"
            rows={1}
            disabled={loading}
            className="flex-1 resize-none text-sm bg-transparent outline-none"
            style={{
              color: "var(--text)",
              maxHeight: "120px",
              overflow: "auto",
            }}
          />
          <button
            onClick={send}
            disabled={loading || !input.trim()}
            className="shrink-0 w-8 h-8 rounded-lg flex items-center justify-center transition-all"
            style={{
              background: input.trim() && !loading ? "var(--accent)" : "var(--surface)",
              opacity: input.trim() && !loading ? 1 : 0.4,
            }}
          >
            <Send size={14} color="white" />
          </button>
        </div>
      </div>
    </div>
  );
}
