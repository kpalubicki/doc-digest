"use client";

import { useEffect, useState } from "react";
import UploadZone from "@/components/UploadZone";
import DocumentList from "@/components/DocumentList";
import ChatBox from "@/components/ChatBox";
import { listDocuments, DocumentInfo } from "@/lib/api";
import { BookOpen } from "lucide-react";

export default function Home() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    listDocuments().then(setDocuments).catch(console.error);
  }, []);

  function onUploaded(doc: DocumentInfo) {
    setDocuments((prev) => [doc, ...prev]);
    setSelectedId(doc.id);
  }

  function onDeleted(id: string) {
    setDocuments((prev) => prev.filter((d) => d.id !== id));
    if (selectedId === id) setSelectedId(null);
  }

  const selectedDoc = documents.find((d) => d.id === selectedId);

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: "var(--background)" }}>
      {/* Sidebar */}
      <aside
        className="w-64 flex flex-col shrink-0 border-r"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
      >
        {/* Logo */}
        <div className="px-5 py-4 border-b flex items-center gap-3" style={{ borderColor: "var(--border)" }}>
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
            style={{ background: "var(--accent)" }}
          >
            <BookOpen size={15} color="white" />
          </div>
          <div>
            <p className="text-sm font-semibold" style={{ color: "var(--text)" }}>doc-digest</p>
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>local Q&A</p>
          </div>
        </div>

        {/* Upload + docs */}
        <div className="flex-1 overflow-y-auto p-4 space-y-5">
          <UploadZone onUploaded={onUploaded} />

          <div>
            <p
              className="text-xs font-medium uppercase tracking-widest mb-2 px-1"
              style={{ color: "var(--text-subtle)", letterSpacing: "0.1em" }}
            >
              Documents
            </p>
            <DocumentList
              documents={documents}
              selectedId={selectedId}
              onSelect={setSelectedId}
              onDeleted={onDeleted}
            />
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t" style={{ borderColor: "var(--border)" }}>
          <p className="text-xs" style={{ color: "var(--text-subtle)" }}>
            Powered by Ollama · runs locally
          </p>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-hidden flex flex-col">
        {documents.length === 0 ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center space-y-3">
              <div
                className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
                style={{ background: "var(--surface-2)" }}
              >
                <BookOpen size={28} style={{ color: "var(--text-subtle)" }} />
              </div>
              <p className="text-base font-medium" style={{ color: "var(--text)" }}>
                No documents yet
              </p>
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                Upload a PDF, TXT, or Markdown file to get started
              </p>
            </div>
          </div>
        ) : (
          <ChatBox documentId={selectedId} documentName={selectedDoc?.filename} />
        )}
      </main>
    </div>
  );
}
