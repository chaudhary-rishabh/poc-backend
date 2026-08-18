from openai import AsyncOpenAI

from app.core.config import settings
from app.services.llm.base import LLMGenerationError

_MODEL = "deepseek-v4-pro"


class DeepSeekProvider:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(base_url="https://api.deepseek.com", api_key=settings.DEEPSEEK_API_KEY)

    async def complete(self, system_prompt: str, user_content: str, max_tokens: int = 4096) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=_MODEL,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
            )
        except Exception as e:
            raise LLMGenerationError(f"DeepSeek API call failed: {e}") from e
        return response.choices[0].message.content or ""

    async def describe_image(self, image_bytes: bytes, mime_type: str) -> str:
        raise LLMGenerationError("DeepSeek does not support image inputs; use AnthropicProvider for vision.")
