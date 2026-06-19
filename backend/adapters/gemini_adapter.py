"""
Google Gemini adapter via the OpenAI-compatible endpoint.
Gemini 1.5+ supports the OpenAI chat completions API format.
"""
from typing import Optional
from backend.adapters.openai_adapter import OpenAIAdapter
from backend.config import settings


class GeminiAdapter(OpenAIAdapter):
    provider = "gemini"
    supports_tool_use = True
    supports_vision = True

    def __init__(self, model: str = "gemini-2.5-flash", api_key: Optional[str] = None):
        super().__init__(
            model=model,
            api_key=api_key or settings.google_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        )
        self.model = model
