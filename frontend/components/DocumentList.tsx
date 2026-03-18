"use client";

import { DocumentInfo, deleteDocument } from "@/lib/api";
import { FileText, FileType, File, X, Layers } from "lucide-react";

interface Props {
  documents: DocumentInfo[];
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  onDeleted: (id: string) => void;
}

function FileIcon({ type }: { type: string }) {
  const props = { size: 13, style: { color: "var(--text-subtle)" } };
  if (type === "pdf") return <FileType {...props} />;
  if (type === "md") return <FileText {...props} />;
  return <File {...props} />;
}

export default function DocumentList({ documents, selectedId, onSelect, onDeleted }: Props) {
  async function handleDelete(e: React.MouseEvent, id: string) {
    e.stopPropagation();
    await deleteDocument(id);
    onDeleted(id);
  }

  if (documents.length === 0) {
    return (
      <p className="text-xs px-1 mt-1" style={{ color: "var(--text-subtle)" }}>
        No documents yet
      </p>
    );
  }

  return (
    <ul className="space-y-0.5">
      <li>
        <button
          onClick={() => onSelect(null)}
          className="w-full text-left text-xs px-2 py-2 rounded-lg flex items-center gap-2 transition-all"
          style={{
            background: selectedId === null ? "rgba(124,58,237,0.15)" : "transparent",
            color: selectedId === null ? "var(--accent)" : "var(--text-muted)",
          }}
        >
          <Layers size={13} />
          <span className="font-medium">All documents</span>
        </button>
      </li>
      {documents.map((doc) => {
        const active = selectedId === doc.id;
        return (
          <li key={doc.id}>
            <button
              onClick={() => onSelect(doc.id)}
              className="w-full text-left text-xs px-2 py-2 rounded-lg flex items-center gap-2 transition-all group"
              style={{
                background: active ? "rgba(124,58,237,0.15)" : "transparent",
                color: active ? "var(--text)" : "var(--text-muted)",
              }}
            >
              <FileIcon type={doc.file_type} />
              <span className="flex-1 truncate font-medium">{doc.filename}</span>
              <span className="shrink-0 text-xs" style={{ color: "var(--text-subtle)" }}>
                {doc.chunk_count}
              </span>
              <span
                onClick={(e) => handleDelete(e, doc.id)}
                className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer hover:text-red-400"
                title="Delete"
                style={{ color: "var(--text-subtle)" }}
              >
                <X size={12} />
              </span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}
