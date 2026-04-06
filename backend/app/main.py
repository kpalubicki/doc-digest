from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.api import documents, chat
from app.api.auth import require_api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_dirs()
    yield


app = FastAPI(
    title="doc-digest",
    description="Chat with your local documents",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/documents", tags=["documents"],
                   dependencies=[Depends(require_api_key)])
app.include_router(chat.router, prefix="/chat", tags=["chat"],
                   dependencies=[Depends(require_api_key)])


@app.get("/health")
def health():
    return {"status": "ok", "model": settings.chat_model}
