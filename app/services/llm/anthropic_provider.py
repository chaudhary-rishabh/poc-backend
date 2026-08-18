import base64
import logging
import ssl

import httpx
import truststore
from anthropic import AsyncAnthropic

from app.core.config import settings
from app.core.model_registry import default_model, model_supports_effort
from app.services.llm.base import LLMGenerationError
from app.services.prompts import SCREENSHOT_VISION_SYSTEM_PROMPT

_PROVIDER_NAME = "anthropic"
_DEFAULT_EFFORT = "medium"

_REQUEST_TIMEOUT_SECONDS = 900.0

logger = logging.getLogger(__name__)


class AnthropicProvider:
    def __init__(self) -> None:
        ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        http_client = httpx.AsyncClient(verify=ssl_context, timeout=_REQUEST_TIMEOUT_SECONDS)
        self._client = AsyncAnthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            http_client=http_client,
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
        create_kwargs = {}
        if model_supports_effort(_PROVIDER_NAME, resolved_model):
            create_kwargs["output_config"] = {"effort": effort or _DEFAULT_EFFORT}
        logger.info("Anthropic call: model=%s effort=%s", resolved_model, create_kwargs.get("output_config"))
        try:
            response = await self._client.messages.create(
                model=resolved_model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}],
                **create_kwargs,
            )
        except Exception as e:
            raise LLMGenerationError(f"Anthropic API call failed: {e}") from e
        return "".join(block.text for block in response.content if block.type == "text")

    async def describe_image(self, image_bytes: bytes, mime_type: str) -> str:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        try:
            response = await self._client.messages.create(
                model=default_model(_PROVIDER_NAME),
                max_tokens=1024,
                system=SCREENSHOT_VISION_SYSTEM_PROMPT,
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
                                "text": "Transcribe this screenshot per your instructions.",
                            },
                        ],
                    }
                ],
            )
        except Exception as e:
            raise LLMGenerationError(f"Anthropic vision call failed: {e}") from e
        return "".join(block.text for block in response.content if block.type == "text")
