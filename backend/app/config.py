from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    embed_model: str = "nomic-embed-text"
    chat_model: str = "qwen2.5:3b"
    chroma_path: str = "./data/chroma"
    upload_path: str = "./data/uploads"
    app_port: int = 8000
    api_key: str | None = None

    model_config = {"env_file": ".env", "extra": "ignore"}

    def ensure_dirs(self):
        Path(self.chroma_path).mkdir(parents=True, exist_ok=True)
        Path(self.upload_path).mkdir(parents=True, exist_ok=True)


settings = Settings()
