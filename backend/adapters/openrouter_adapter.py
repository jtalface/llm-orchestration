"""
OpenRouter adapter — access 300+ models through a single OpenAI-compatible API.
Model IDs look like: "anthropic/claude-opus-4-8", "meta-llama/llama-3.3-70b-instruct", etc.
"""
from typing import Optional
from backend.adapters.openai_adapter import OpenAIAdapter
from backend.config import settings


class OpenRouterAdapter(OpenAIAdapter):
    provider = "openrouter"
    supports_tool_use = True

    def __init__(self, model: str = "anthropic/claude-sonnet-4-6", api_key: Optional[str] = None):
        super().__init__(
            model=model,
            api_key=api_key or settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        self.model = model
