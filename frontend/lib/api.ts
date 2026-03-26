const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface DocumentInfo {
  id: string;
  filename: string;
  file_type: string;
  chunk_count: number;
  uploaded_at: string;
}

export interface Source {
  document_id: string;
  filename: string;
  chunk: string;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
}

export async function uploadDocument(file: File): Promise<DocumentInfo> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/documents`, { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail ?? "Upload failed");
  }
  return res.json();
}

export async function listDocuments(): Promise<DocumentInfo[]> {
  const res = await fetch(`${BASE}/documents`);
  if (!res.ok) throw new Error("Failed to fetch documents");
  const data = await res.json();
  return data.documents;
}

export async function deleteDocument(id: string): Promise<void> {
  const res = await fetch(`${BASE}/documents/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Delete failed");
}

export async function askQuestion(
  question: string,
  documentId?: string
): Promise<ChatResponse> {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, document_id: documentId ?? null }),
  });
  if (!res.ok) throw new Error("Chat request failed");
  return res.json();
}

export async function askQuestionStream(
  question: string,
  documentId: string | undefined,
  onToken: (token: string) => void,
  onDone: (sources: Source[]) => void
): Promise<void> {
  const res = await fetch(`${BASE}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, document_id: documentId ?? null }),
  });

  if (!res.ok || !res.body) throw new Error("Stream request failed");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const payload = JSON.parse(line.slice(6));
      if (payload.token) onToken(payload.token);
      if (payload.done) onDone(payload.sources ?? []);
    }
  }
}
