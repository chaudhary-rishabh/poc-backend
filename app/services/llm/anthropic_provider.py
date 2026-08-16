import base64
import json

from anthropic import AsyncAnthropic
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.services.llm.base import LLMGenerationError

_JSON_ONLY_INSTRUCTION = (
    "\n\nReturn ONLY raw JSON matching the required schema. "
    "No markdown code fences, no preamble, no explanation — JSON only."
)

_MODEL = "claude-sonnet-4-5"


class AnthropicProvider:
    def __init__(self) -> None:
        self._client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

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
                raise LLMGenerationError(f"Anthropic response failed validation after retry: {e2}") from e2

    async def _complete(self, system: str, user_content: str) -> str:
        try:
            response = await self._client.messages.create(
                model=_MODEL,
                max_tokens=4096,
                system=system,
                messages=[{"role": "user", "content": user_content}],
            )
        except Exception as e:
            raise LLMGenerationError(f"Anthropic API call failed: {e}") from e
        return "".join(block.text for block in response.content if block.type == "text")

    async def describe_image(self, image_bytes: bytes, mime_type: str) -> str:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        try:
            response = await self._client.messages.create(
                model=_MODEL,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {"type": "base64", "media_type": mime_type, "data": b64},
                            },
                            {
                                "type": "text",
                                "text": (
                                    "Describe this screenshot in detail for a business analyst who needs to "
                                    "understand the current or proposed workflow it depicts. Include visible "
                                    "text, UI elements, and layout."
                                ),
                            },
                        ],
                    }
                ],
            )
        except Exception as e:
            raise LLMGenerationError(f"Anthropic vision call failed: {e}") from e
        return "".join(block.text for block in response.content if block.type == "text")


def _parse_json(raw: str):
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    return json.loads(cleaned.strip())
