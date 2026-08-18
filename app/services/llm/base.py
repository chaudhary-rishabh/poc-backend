from typing import Protocol


class LLMGenerationError(Exception):
    pass


class LLMProvider(Protocol):
    async def complete(
        self,
        system_prompt: str,
        user_content: str,
        max_tokens: int = 4096,
        model: str | None = None,
        effort: str | None = None,
    ) -> str:
        """Call the model and return its raw text response. No JSON parsing or
        validation here — that's shared across providers in doc_generation.py.

        model/effort default to the provider's own default model and "medium"
        effort when omitted. effort is ignored for models that don't support it."""
        ...

    async def describe_image(self, image_bytes: bytes, mime_type: str) -> str: ...
