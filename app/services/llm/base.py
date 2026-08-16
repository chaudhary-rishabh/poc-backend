from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMGenerationError(Exception):
    pass


class LLMProvider(Protocol):
    async def generate_structured(self, system_prompt: str, user_content: str, response_model: type[T]) -> T: ...

    async def describe_image(self, image_bytes: bytes, mime_type: str) -> str: ...
