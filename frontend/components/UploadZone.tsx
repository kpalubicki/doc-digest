"use client";

import { useRef, useState } from "react";
import { uploadDocument, DocumentInfo } from "@/lib/api";
import { Upload } from "lucide-react";

interface Props {
  onUploaded: (doc: DocumentInfo) => void;
}

export default function UploadZone({ onUploaded }: Props) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFile(file: File) {
    setUploading(true);
    setError(null);
    try {
      const doc = await uploadDocument(file);
      onUploaded(doc);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      onClick={() => !uploading && inputRef.current?.click()}
      className="rounded-xl p-4 text-center cursor-pointer transition-all border-2 border-dashed"
      style={{
        background: dragging ? "rgba(124,58,237,0.08)" : "var(--surface-2)",
        borderColor: dragging ? "var(--accent)" : "var(--border)",
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.txt,.md"
        className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
      />
      {uploading ? (
        <div className="flex items-center justify-center gap-2 py-1">
          <div
            className="w-4 h-4 rounded-full border-2 border-t-transparent animate-spin"
            style={{ borderColor: "var(--accent)", borderTopColor: "transparent" }}
          />
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>Uploading…</span>
        </div>
      ) : (
        <div className="py-1">
          <Upload size={16} className="mx-auto mb-1.5" style={{ color: "var(--text-subtle)" }} />
          <p className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>
            Drop file or click to browse
          </p>
          <p className="text-xs mt-0.5" style={{ color: "var(--text-subtle)" }}>PDF · TXT · MD</p>
        </div>
      )}
      {error && (
        <p className="text-xs mt-2" style={{ color: "#ef4444" }}>{error}</p>
      )}
    </div>
  );
}
