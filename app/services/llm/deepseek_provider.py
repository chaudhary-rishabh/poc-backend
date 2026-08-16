import json

from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

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

    async def generate_structured(self, system_prompt: str, user_content: str, response_model: type[BaseModel]):
        system = system_prompt + _JSON_ONLY_INSTRUCTION
        raw = await self._complete(system, user_content)

        try:
            return response_model.model_validate(_parse_json(raw))
        except (ValidationError, json.JSONDecodeError) as e:
            retry_user_content = (
                f"{user_content}\n\nYour previous response failed validation: {e}. "
                "Return corrected JSON only."
            )
            raw_retry = await self._complete(system, retry_user_content)
            try:
                return response_model.model_validate(_parse_json(raw_retry))
            except (ValidationError, json.JSONDecodeError) as e2:
                raise LLMGenerationError(f"DeepSeek response failed validation after retry: {e2}") from e2

    async def _complete(self, system: str, user_content: str) -> str:
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


def _parse_json(raw: str):
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    return json.loads(cleaned.strip())
