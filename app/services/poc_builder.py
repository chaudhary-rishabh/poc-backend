import json
import random
from pathlib import Path

from app.schemas.doc_b import DocB
from app.services.llm.base import LLMGenerationError, LLMProvider
from app.services.prompts import POC_TEMPLATE_FILL_SYSTEM_PROMPT, build_retry_suffix

_SKELETON_PATH = Path(__file__).resolve().parent.parent / "templates" / "poc_skeleton.html"

LAYOUT_ARCHETYPES = [
    "left sidebar navigation with a top bar",
    "horizontal top tab bar, no sidebar, content fills full width",
    "split-pane: a list/filter panel on the left, detail panel on the right, no top-level nav at all",
    "single-column stacked sections with sticky section headers, no persistent nav chrome",
    "card-grid dashboard as the home view, with screens reached by clicking into a card rather than a nav menu",
]

MOOD_DIRECTIONS = [
    "clean and minimal, generous whitespace, low visual weight",
    "dense and data-forward, compact rows, information-dense tables",
    "warm and approachable, soft surfaces, rounded everything",
    "crisp and structured, sharper edges, clear grid lines",
]


def build_poc_user_content(skeleton_html: str, doc_b_json: str) -> str:
    layout = random.choice(LAYOUT_ARCHETYPES)
    mood = random.choice(MOOD_DIRECTIONS)
    design_direction = (
        f"Design direction for this generation (follow exactly, do not default to a "
        f"left-sidebar admin-panel layout unless it's the one chosen below):\n"
        f"- Layout: {layout}\n"
        f"- Mood: {mood}\n"
        f"- Derive the accent color from the business domain below, not from a fixed default."
    )
    return f"{design_direction}\n\nSKELETON:\n{skeleton_html}\n\nDOC B:\n{doc_b_json}"


async def build_poc_html(provider: LLMProvider, doc_b: DocB) -> str:
    skeleton = _SKELETON_PATH.read_text(encoding="utf-8")
    doc_b_json = json.dumps(doc_b.model_dump())

    user_content = build_poc_user_content(skeleton, doc_b_json)

    max_tokens = 16000

    html = await provider.complete(POC_TEMPLATE_FILL_SYSTEM_PROMPT, user_content, max_tokens=max_tokens)
    html = _strip_markdown_fence(html)

    if not _looks_like_valid_html(html):
        retry_content = user_content + build_retry_suffix(
            "Response was not a well-formed HTML document containing the expected React root "
            "mount call. Return the complete HTML file only, starting with <!DOCTYPE html> and "
            "ending with </html>."
        )
        html = await provider.complete(POC_TEMPLATE_FILL_SYSTEM_PROMPT, retry_content, max_tokens=max_tokens)
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
