from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""
    openrouter_api_key: str = ""
    tavily_api_key: str = ""

    # Ollama
    ollama_base_url: str = "http://localhost:11434"

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True

    # Storage
    db_path: str = "./data/db.sqlite"
    chroma_path: str = "./data/chroma"
    artifacts_path: str = "./data/artifacts"

    # Agent defaults
    default_model: str = "claude-sonnet-4-6"
    default_max_steps: int = 50
    default_max_tokens: int = 8192
    context_window_budget: int = 100_000

    def ensure_dirs(self):
        for path_str in [self.db_path, self.chroma_path, self.artifacts_path]:
            Path(path_str).parent.mkdir(parents=True, exist_ok=True)
        Path(self.chroma_path).mkdir(parents=True, exist_ok=True)
        Path(self.artifacts_path).mkdir(parents=True, exist_ok=True)


settings = Settings()
