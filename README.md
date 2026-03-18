# doc-digest

Upload a document. Ask questions about it. Get answers with source citations.

Runs entirely on your machine — Ollama handles the embeddings and the LLM. No API keys, no data sent anywhere.

![Python](https://img.shields.io/badge/python-3.11+-blue) ![Next.js](https://img.shields.io/badge/next.js-16-black) ![Ollama](https://img.shields.io/badge/ollama-local-green)

---

## Why

I got tired of copy-pasting chunks of PDFs into ChatGPT every time I had a question about a contract or a technical spec. This does the same thing but runs offline and keeps your files on your own hardware.

## How it works

1. Drop a PDF, TXT, or Markdown file into the sidebar
2. The backend splits it into chunks, embeds them with `nomic-embed-text`, stores them in ChromaDB
3. You ask a question — it finds the most relevant chunks, passes them as context to `qwen2.5:3b`, and returns an answer with source references

You can query across all uploaded documents at once, or pin the chat to a specific file.

---

## Stack

- **Backend** — Python 3.11+, FastAPI, ChromaDB, Ollama, PyPDF
- **Frontend** — Next.js 16, TypeScript, Tailwind CSS
- **Models** — `nomic-embed-text` (embeddings), `qwen2.5:3b` (chat)

---

## Quick start

You need [Ollama](https://ollama.ai/) installed and running.

```bash
ollama pull nomic-embed-text
ollama pull qwen2.5:3b
```

**Backend:**

```bash
cd backend
pip install fastapi uvicorn python-multipart pypdf chromadb ollama python-dotenv aiofiles
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

**Or use Docker:**

```bash
cp .env.example backend/.env
docker compose up --build
```

Ollama needs to be running on the host. The Docker setup connects via `host.docker.internal`.

---

## Configuration

Edit `backend/.env`:

```bash
OLLAMA_BASE_URL=http://localhost:11434
EMBED_MODEL=nomic-embed-text
CHAT_MODEL=qwen2.5:3b
CHROMA_PATH=./data/chroma
UPLOAD_PATH=./data/uploads
```

Swap the models for anything else you have pulled locally — the only requirement is Ollama compatibility.

---

## Tests

```bash
cd backend
pip install pytest httpx
pytest tests/ -v
```

---

## API

Swagger UI at [http://localhost:8000/docs](http://localhost:8000/docs)

```
POST   /documents        upload a file
GET    /documents        list all documents
GET    /documents/{id}   document info
DELETE /documents/{id}   remove document and embeddings
POST   /chat             ask a question
```

---

## License

MIT
