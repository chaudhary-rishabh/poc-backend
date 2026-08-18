import json
import random
from pathlib import Path

from app.schemas.doc_b import DocB
from app.services.llm.base import LLMGenerationError, LLMProvider
from app.services.prompts import POC_TEMPLATE_FILL_SYSTEM_PROMPT, build_retry_suffix

_SKELETON_PATH = Path(__file__).resolve().parent.parent / "templates" / "poc_skeleton.html"

LAYOUT_ARCHETYPES = [
    "left sidebar navigation (must be collapsible) with a top bar",
    "horizontal top tab bar, no sidebar, content fills full width",
    "split-pane: a list/filter panel on the left, detail panel on the right, no top-level nav at all",
    "single-column stacked sections with sticky section headers, no persistent nav chrome",
    "card-grid dashboard as the home view, with screens reached by clicking into a card rather than a nav menu",
]

PALETTE_DIRECTIONS = [
    "white background, black text, deep forest-green accent",
    "white background, black text, no accent color (pure monochrome)",
    "white background, black text, warm orange accent",
    "white background, dark charcoal text, cool grey as the primary structural color, no separate accent",
    "black/near-black background, white text, single white or light-grey accent (dark mode)",
]

HEADING_FONTS = ["Lusitana", "Noto Serif", "Lora"]
BODY_FONTS = ["Inter", "Source Sans 3"]


def build_poc_user_content(
    skeleton_html: str,
    doc_b_json: str,
    feedback: str | None = None,
    current_poc_html: str | None = None,
) -> str:
    if current_poc_html:
        # Regenerating from feedback: keep the existing design direction stable
        # rather than re-rolling it, so the output stays a revision, not a redo.
        design_direction = (
            f"Design direction for this generation: preserve the layout, palette, and fonts "
            f"already used in the CURRENT VERSION below exactly as they are — this is a revision, "
            f"not a fresh design.\n"
            f"- If the layout includes a sidebar, it must remain collapsible via a real toggle.\n"
            f"- No emoji or icon-font glyphs — minimal inline SVG line icons only, used sparingly."
        )
    else:
        layout = random.choice(LAYOUT_ARCHETYPES)
        palette = random.choice(PALETTE_DIRECTIONS)
        heading_font = random.choice(HEADING_FONTS)
        body_font = random.choice(BODY_FONTS)

        design_direction = (
            f"Design direction for this generation (follow exactly):\n"
            f"- Layout: {layout}\n"
            f"- Palette: {palette} — use this palette unless Doc B's domain strongly suggests a "
            f"better fit among the five approved palettes in your system prompt; if so, prefer the "
            f"domain-appropriate one instead.\n"
            f"- Heading font: use `font-heading` for all titles/headers, which resolves to {heading_font} "
            f"(already loaded).\n"
            f"- Body font: use `font-body` for all body/data text, which resolves to {body_font} "
            f"(already loaded).\n"
            f"- If the layout includes a sidebar, it must be collapsible via a real toggle.\n"
            f"- No emoji or icon-font glyphs — minimal inline SVG line icons only, used sparingly."
        )

    user_content = f"{design_direction}\n\nSKELETON:\n{skeleton_html}\n\nDOC B:\n{doc_b_json}"

    if current_poc_html:
        user_content += (
            f"\n\nCURRENT VERSION (this is the baseline to revise, not a fresh input to ignore):\n"
            f"{current_poc_html}"
        )
    if feedback:
        user_content += (
            f"\n\nUSER FEEDBACK (required correction — apply it directly to the current version above):\n"
            f"{feedback}"
        )
    return user_content


async def build_poc_html(
    provider: LLMProvider,
    doc_b: DocB,
    feedback: str | None = None,
    current_poc_html: str | None = None,
    model: str | None = None,
    effort: str | None = None,
) -> str:
    skeleton = _SKELETON_PATH.read_text(encoding="utf-8")
    doc_b_json = json.dumps(doc_b.model_dump())

    user_content = build_poc_user_content(skeleton, doc_b_json, feedback, current_poc_html)

    max_tokens = 16000

    html = await provider.complete(
        POC_TEMPLATE_FILL_SYSTEM_PROMPT, user_content, max_tokens=max_tokens, model=model, effort=effort
    )
    html = _strip_markdown_fence(html)

    if not _looks_like_valid_html(html):
        retry_content = user_content + build_retry_suffix(
            "Response was not a well-formed HTML document containing the expected React root "
            "mount call. Return the complete HTML file only, starting with <!DOCTYPE html> and "
            "ending with </html>."
        )
        html = await provider.complete(
            POC_TEMPLATE_FILL_SYSTEM_PROMPT, retry_content, max_tokens=max_tokens, model=model, effort=effort
        )
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