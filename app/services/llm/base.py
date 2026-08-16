from typing import Protocol


class LLMGenerationError(Exception):
    pass


class LLMProvider(Protocol):
    async def complete(self, system_prompt: str, user_content: str, max_tokens: int = 4096) -> str:
        """Call the model and return its raw text response. No JSON parsing or
        validation here — that's shared across providers in doc_generation.py."""
        ...

    async def describe_image(self, image_bytes: bytes, mime_type: str) -> str: ...
