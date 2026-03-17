"use client";

import { useEffect, useState } from "react";
import UploadZone from "@/components/UploadZone";
import DocumentList from "@/components/DocumentList";
import ChatBox from "@/components/ChatBox";
import { listDocuments, DocumentInfo } from "@/lib/api";

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
    <div className="flex h-screen bg-white">
      {/* Sidebar */}
      <aside className="w-64 border-r flex flex-col shrink-0">
        <div className="p-4 border-b">
          <h1 className="font-semibold text-gray-800">doc-digest</h1>
          <p className="text-xs text-gray-400 mt-0.5">local document Q&A</p>
        </div>

        <div className="p-4 flex-1 overflow-y-auto">
          <UploadZone onUploaded={onUploaded} />

          <div className="mt-4">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
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
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-hidden">
        {documents.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-400">
            <div className="text-center">
              <p className="text-lg">Upload a document to get started</p>
              <p className="text-sm mt-1">PDF, TXT, and Markdown are supported</p>
            </div>
          </div>
        ) : (
          <ChatBox documentId={selectedId} documentName={selectedDoc?.filename} />
        )}
      </main>
    </div>
  );
}
