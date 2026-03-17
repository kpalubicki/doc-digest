"use client";

import { DocumentInfo, deleteDocument } from "@/lib/api";

interface Props {
  documents: DocumentInfo[];
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  onDeleted: (id: string) => void;
}

export default function DocumentList({ documents, selectedId, onSelect, onDeleted }: Props) {
  async function handleDelete(e: React.MouseEvent, id: string) {
    e.stopPropagation();
    await deleteDocument(id);
    onDeleted(id);
  }

  if (documents.length === 0) {
    return <p className="text-sm text-gray-400 mt-2">No documents yet</p>;
  }

  return (
    <ul className="mt-2 space-y-1">
      <li>
        <button
          onClick={() => onSelect(null)}
          className={`w-full text-left text-sm px-3 py-2 rounded-md transition-colors ${
            selectedId === null
              ? "bg-blue-100 text-blue-800"
              : "text-gray-600 hover:bg-gray-100"
          }`}
        >
          All documents
        </button>
      </li>
      {documents.map((doc) => (
        <li key={doc.id}>
          <button
            onClick={() => onSelect(doc.id)}
            className={`w-full text-left text-sm px-3 py-2 rounded-md transition-colors group flex items-start justify-between gap-2 ${
              selectedId === doc.id
                ? "bg-blue-100 text-blue-800"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            <span className="truncate">
              <span className="block font-medium truncate">{doc.filename}</span>
              <span className="text-xs text-gray-400">{doc.chunk_count} chunks</span>
            </span>
            <span
              onClick={(e) => handleDelete(e, doc.id)}
              className="text-gray-300 hover:text-red-400 text-xs mt-0.5 shrink-0 cursor-pointer"
              title="Delete"
            >
              ✕
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}
