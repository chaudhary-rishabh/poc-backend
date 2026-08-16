from app.core.config import settings
from app.services.llm.anthropic_provider import AnthropicProvider
from app.services.llm.base import LLMProvider
from app.services.llm.deepseek_provider import DeepSeekProvider

# Providers are constructed lazily (not at import time) so the app can start even if
# only one provider's API key is configured, and so a missing key surfaces as a clean
# error on the specific request that needs it rather than crashing the whole process.
_anthropic: AnthropicProvider | None = None
_deepseek: DeepSeekProvider | None = None


def get_provider(name: str | None) -> LLMProvider:
    global _anthropic, _deepseek

    resolved = (name or settings.LLM_PROVIDER).lower()
    if resolved == "anthropic":
        if _anthropic is None:
            _anthropic = AnthropicProvider()
        return _anthropic
    if resolved == "deepseek":
        if _deepseek is None:
            _deepseek = DeepSeekProvider()
        return _deepseek
    raise ValueError(f"Unknown LLM provider: {resolved}")
