# doc-digest

Pasting a 40-page PDF into ChatGPT burns through tokens fast and you hit context limits before you're done. The document also ends up on someone else's server. Running it locally on Ollama is free and nothing leaves your machine.

Upload a file, ask questions, get answers with citations back to the source text.

## how it works

Drop a file into the sidebar. The backend splits it into chunks, embeds them with `nomic-embed-text`, and stores everything in ChromaDB locally. Ask a question and it finds the closest chunks, passes them as context to `qwen2.5:3b`, and returns an answer alongside the source excerpts it used.

You can chat against all your documents at once, or pin the conversation to one file.

## quick start

Needs Ollama running. Pull the two models first:

```bash
ollama pull nomic-embed-text
ollama pull qwen2.5:3b
```

Backend:

```bash
cd backend
pip install fastapi uvicorn python-multipart pypdf chromadb ollama python-dotenv aiofiles
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

Docker works too:

```bash
cp .env.example backend/.env
docker compose up --build
```

The compose file connects to Ollama via `host.docker.internal`, so Ollama needs to be running on the host, not in a container.

## configuration

`backend/.env`:

```bash
OLLAMA_BASE_URL=http://localhost:11434
EMBED_MODEL=nomic-embed-text
CHAT_MODEL=qwen2.5:3b
CHROMA_PATH=./data/chroma
UPLOAD_PATH=./data/uploads
```

Any Ollama-compatible model works. `llama3.2:3b` is a reasonable alternative if you want something lighter.

## tests

```bash
cd backend
pip install pytest httpx
pytest tests/ -v
```

## API

Swagger at http://localhost:8000/docs

```
POST   /documents        upload a file
GET    /documents        list all documents
GET    /documents/{id}   document info
DELETE /documents/{id}   remove document and embeddings
POST   /chat             ask a question
POST   /chat/stream      same, but streamed as SSE
```

## troubleshooting

**"Something went wrong — make sure Ollama is running"**
Ollama isn't running or the model isn't pulled. Run `ollama serve` and then `ollama pull qwen2.5:3b && ollama pull nomic-embed-text`.

**Port 8000 or 3000 already in use**
Set `APP_PORT=8001` in `backend/.env` and update `NEXT_PUBLIC_API_URL=http://localhost:8001` in `frontend/.env.local`.

**Docker: Ollama not reachable from container**
The compose file uses `host.docker.internal` which works on Windows and Mac. On Linux, replace it with your host IP or run Ollama inside Docker too.

## stack

Python 3.11+, FastAPI, ChromaDB, Ollama, PyPDF, Next.js 16, TypeScript, Tailwind

## license

MIT
