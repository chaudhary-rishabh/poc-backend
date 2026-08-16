from fastapi import UploadFile
from pypdf import PdfReader
import io

from app.services.llm.anthropic_provider import AnthropicProvider

_SCREENSHOT_MIME_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"}

# Screenshot description always uses Anthropic's vision call, regardless of the
# selected text-generation provider — DeepSeek's chat API has no image input support.
# This is a hardcoded exception, not something driven by the request's `provider` field.
# Constructed lazily so importing this module doesn't require ANTHROPIC_API_KEY to be set.
_vision_provider: AnthropicProvider | None = None


def _get_vision_provider() -> AnthropicProvider:
    global _vision_provider
    if _vision_provider is None:
        _vision_provider = AnthropicProvider()
    return _vision_provider


async def build_combined_text(files: list[UploadFile], text: str | None) -> str:
    sections: list[str] = []

    if text:
        sections.append(f"[source: pasted_text]\n{text.strip()}")

    for f in files:
        content = await f.read()
        mime = f.content_type or ""

        if mime in _SCREENSHOT_MIME_TYPES or _looks_like_image(f.filename):
            description = await _get_vision_provider().describe_image(content, mime or "image/png")
            sections.append(f"[source: {f.filename}]\n{description}")
        elif mime == "application/pdf" or (f.filename or "").lower().endswith(".pdf"):
            extracted = _extract_pdf_text(content)
            sections.append(f"[source: {f.filename}]\n{extracted}")
        else:
            try:
                decoded = content.decode("utf-8")
            except UnicodeDecodeError:
                decoded = "[unreadable binary content]"
            sections.append(f"[source: {f.filename}]\n{decoded}")

    return "\n\n".join(sections)


def _looks_like_image(filename: str | None) -> bool:
    if not filename:
        return False
    return filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif"))


def _extract_pdf_text(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)
