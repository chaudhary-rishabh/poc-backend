import json
from pathlib import Path

from app.schemas.doc_b import DocB
from app.services.llm.base import LLMGenerationError, LLMProvider
from app.services.prompts import POC_TEMPLATE_FILL_SYSTEM_PROMPT, build_retry_suffix

_SKELETON_PATH = Path(__file__).resolve().parent.parent / "templates" / "poc_skeleton.html"


async def build_poc_html(provider: LLMProvider, doc_b: DocB) -> str:
    skeleton = _SKELETON_PATH.read_text(encoding="utf-8")
    doc_b_json = json.dumps(doc_b.model_dump())

    user_content = f"SKELETON:\n{skeleton}\n\nDOC B:\n{doc_b_json}"

    html = await provider.complete(POC_TEMPLATE_FILL_SYSTEM_PROMPT, user_content)
    html = _strip_markdown_fence(html)

    if not _looks_like_valid_html(html):
        retry_content = user_content + build_retry_suffix(
            "Response was not a well-formed HTML document containing the expected React root "
            "mount call. Return the complete HTML file only, starting with <!DOCTYPE html> and "
            "ending with </html>."
        )
        html = await provider.complete(POC_TEMPLATE_FILL_SYSTEM_PROMPT, retry_content)
        html = _strip_markdown_fence(html)
        if not _looks_like_valid_html(html):
            raise LLMGenerationError("POC template-fill failed validation after retry: malformed HTML output.")

    return html


def _strip_markdown_fence(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("html"):
            cleaned = cleaned[4:]
    return cleaned.strip()


def _looks_like_valid_html(html: str) -> bool:
    lower = html.lower()
    return "<!doctype html>" in lower and "</html>" in lower and "reactdom.createroot" in lower
