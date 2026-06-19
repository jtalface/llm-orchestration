from backend.adapters.base import BaseLLMAdapter, Message, StreamEvent, StreamEventType, CompletionResult, ToolCall
from backend.adapters.anthropic_adapter import AnthropicAdapter
from backend.adapters.openai_adapter import OpenAIAdapter
from backend.adapters.ollama_adapter import OllamaAdapter
from backend.adapters.openrouter_adapter import OpenRouterAdapter
from backend.adapters.gemini_adapter import GeminiAdapter


# Model ID prefix → adapter class
_REGISTRY: dict[str, type] = {
    "claude": AnthropicAdapter,
    "gpt": OpenAIAdapter,
    "o1": OpenAIAdapter,
    "o3": OpenAIAdapter,
    "gemini": GeminiAdapter,
    "llama": OllamaAdapter,
    "mistral": OllamaAdapter,
    "qwen": OllamaAdapter,
    "phi": OllamaAdapter,
    "deepseek": OllamaAdapter,
}


def get_adapter(model_id: str) -> BaseLLMAdapter:
    """
    Resolve a model ID string to the correct adapter instance.

    Examples:
        "claude-sonnet-4-6"          → AnthropicAdapter
        "gpt-4o"                     → OpenAIAdapter
        "gemini-2.5-flash"           → GeminiAdapter
        "llama3.2"                   → OllamaAdapter (local)
        "anthropic/claude-opus-4-8"  → OpenRouterAdapter
    """
    if "/" in model_id:
        return OpenRouterAdapter(model=model_id)

    for prefix, cls in _REGISTRY.items():
        if model_id.startswith(prefix):
            return cls(model=model_id)

    return OllamaAdapter(model=model_id)


__all__ = [
    "BaseLLMAdapter", "Message", "StreamEvent", "StreamEventType",
    "CompletionResult", "ToolCall",
    "AnthropicAdapter", "OpenAIAdapter", "OllamaAdapter",
    "OpenRouterAdapter", "GeminiAdapter",
    "get_adapter",
]
