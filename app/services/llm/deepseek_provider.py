from openai import AsyncOpenAI

from app.core.config import settings
from app.services.llm.base import LLMGenerationError

_JSON_ONLY_INSTRUCTION = (
    "\n\nReturn ONLY raw JSON matching the required schema. "
    "No markdown code fences, no preamble, no explanation — JSON only."
)

_MODEL = "deepseek-chat"


class DeepSeekProvider:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(base_url="https://api.deepseek.com", api_key=settings.DEEPSEEK_API_KEY)

    async def complete(self, system_prompt: str, user_content: str) -> str:
        system = system_prompt + _JSON_ONLY_INSTRUCTION
        try:
            response = await self._client.chat.completions.create(
                model=_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_content},
                ],
            )
        except Exception as e:
            raise LLMGenerationError(f"DeepSeek API call failed: {e}") from e
        return response.choices[0].message.content or ""

    async def describe_image(self, image_bytes: bytes, mime_type: str) -> str:
        # DeepSeek's chat API has no vision input support. Screenshot description must
        # always route through AnthropicProvider regardless of the selected text provider —
        # enforced in ingestion.py, not here, so this stays a hard failure if ever called directly.
        raise LLMGenerationError("DeepSeek does not support image inputs; use AnthropicProvider for vision.")
