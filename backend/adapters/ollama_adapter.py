"""
Ollama adapter — uses the OpenAI-compatible API that Ollama exposes at /v1.
Any model pulled via `ollama pull <name>` is available.
"""
from typing import Optional
from backend.adapters.openai_adapter import OpenAIAdapter
from backend.config import settings


class OllamaAdapter(OpenAIAdapter):
    provider = "ollama"
    supports_tool_use = True  # Ollama supports tool use for models that were trained for it
    supports_vision = False

    def __init__(self, model: str = "llama3.2", base_url: Optional[str] = None):
        super().__init__(
            model=model,
            api_key="ollama",  # Ollama doesn't need a real key
            base_url=f"{base_url or settings.ollama_base_url}/v1",
        )
        self.model = model
