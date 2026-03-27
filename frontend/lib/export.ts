interface Source {
  filename: string;
  chunk: string;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
}

export function exportChatAsMarkdown(messages: Message[], documentName?: string): void {
  const title = documentName ? `Chat: ${documentName}` : "Chat: all documents";
  const date = new Date().toISOString().slice(0, 10);

  const lines: string[] = [
    `# ${title}`,
    `_exported ${date}_`,
    "",
  ];

  for (const msg of messages) {
    if (msg.role === "user") {
      lines.push(`**Q:** ${msg.content}`, "");
    } else {
      lines.push(`**A:** ${msg.content}`, "");
      if (msg.sources && msg.sources.length > 0) {
        lines.push("_Sources:_");
        for (const s of msg.sources) {
          lines.push(`- **${s.filename}**: ${s.chunk.slice(0, 150)}...`);
        }
        lines.push("");
      }
    }
  }

  const blob = new Blob([lines.join("\n")], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `chat-${date}.md`;
  a.click();
  URL.revokeObjectURL(url);
}
