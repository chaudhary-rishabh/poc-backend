import base64
import ssl

import httpx
import truststore
from anthropic import AsyncAnthropic

from app.core.config import settings
from app.services.llm.base import LLMGenerationError
from app.services.prompts import SCREENSHOT_VISION_SYSTEM_PROMPT

_MODEL = "claude-sonnet-4-5"


class AnthropicProvider:
    def __init__(self) -> None:
        ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        http_client = httpx.AsyncClient(verify=ssl_context)
        self._client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY, http_client=http_client)

    async def complete(self, system_prompt: str, user_content: str, max_tokens: int = 4096) -> str:
        try:
            response = await self._client.messages.create(
                model=_MODEL,
                max_tokens=max_tokens,
                system=system_prompt,
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
