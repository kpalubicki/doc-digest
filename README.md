# doc-digest

Upload a document. Ask questions about it. Get answers with source citations.

Everything runs locally — Ollama handles the embeddings and the LLM. No API keys, no data sent anywhere, no cloud costs.

---

## How it works

1. Drop a PDF, TXT, or Markdown file into the sidebar
2. The backend splits it into chunks, embeds them with `nomic-embed-text`, and stores them in ChromaDB
3. You ask a question — it finds the most relevant chunks, passes them as context to `qwen2.5:3b-instruct`, and streams back an answer with source references

You can search across all uploaded documents at once, or pin the chat to a specific file.

---

## Stack

- **Backend** — Python 3.11, FastAPI, ChromaDB, Ollama, PyPDF
- **Frontend** — Next.js 15, TypeScript, Tailwind CSS
- **Models** — `nomic-embed-text` (embeddings), `qwen2.5:3b-instruct` (chat)

---

## Quick start

You need [Ollama](https://ollama.ai/) installed and running.

```bash
ollama pull nomic-embed-text
ollama pull qwen2.5:3b-instruct
```

### Option 1 — run locally (Windows)

```powershell
cd backend
cp ..\.env.example .env
.\run.ps1
```

Then in another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

### Option 2 — Docker

```bash
cp .env.example backend/.env
docker compose up --build
```

Open http://localhost:3000

Ollama needs to be running on the host. The Docker setup connects to it via `host.docker.internal`.

---

## Configuration

Edit `backend/.env`:

```bash
OLLAMA_BASE_URL=http://localhost:11434
EMBED_MODEL=nomic-embed-text
CHAT_MODEL=qwen2.5:3b-instruct
CHROMA_PATH=./data/chroma
UPLOAD_PATH=./data/uploads
APP_PORT=8000
```

Swap the models if you have something else pulled — any Ollama-compatible model works.

---

## API

The backend exposes a Swagger UI at http://localhost:8000/docs

```
POST /documents          upload a document
GET  /documents          list all documents
GET  /documents/{id}     document details
DELETE /documents/{id}   remove document and its embeddings
POST /chat               ask a question
```

---

## License

MIT
