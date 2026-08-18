import logging

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.model_registry import default_model, model_supports_effort
from app.services.llm.base import LLMGenerationError

_PROVIDER_NAME = "deepseek"
_DEFAULT_EFFORT = "medium"

# Our registry's effort levels (low/medium/high) map onto DeepSeek's
# thinking.reasoning_effort values (low/high/max) — DeepSeek has no "medium",
# and its docs note unrecognized values fall back to "high" server-side, so we
# map explicitly rather than rely on that fallback.
_EFFORT_MAP = {"low": "low", "medium": "high", "high": "max"}

_REQUEST_TIMEOUT_SECONDS = 900.0

logger = logging.getLogger(__name__)


class DeepSeekProvider:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            base_url="https://api.deepseek.com",
            api_key=settings.DEEPSEEK_API_KEY,
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )

    async def complete(
        self,
        system_prompt: str,
        user_content: str,
        max_tokens: int = 4096,
        model: str | None = None,
        effort: str | None = None,
    ) -> str:
        resolved_model = model or default_model(_PROVIDER_NAME)
        extra_body = {}
        if model_supports_effort(_PROVIDER_NAME, resolved_model):
            reasoning_effort = _EFFORT_MAP.get(effort or _DEFAULT_EFFORT, "high")
            extra_body["thinking"] = {"type": "enabled", "reasoning_effort": reasoning_effort}
        logger.info("DeepSeek call: model=%s thinking=%s", resolved_model, extra_body.get("thinking"))
        try:
            response = await self._client.chat.completions.create(
                model=resolved_model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                extra_body=extra_body,
            )
        except Exception as e:
            raise LLMGenerationError(f"DeepSeek API call failed: {e}") from e
        return response.choices[0].message.content or ""

    async def describe_image(self, image_bytes: bytes, mime_type: str) -> str:
        raise LLMGenerationError("DeepSeek does not support image inputs; use AnthropicProvider for vision.")
