"""Model/effort registry the frontend fetches via GET /models to build its
dropdowns — nothing about model options should be hardcoded client-side.

deprecated: True means no longer officially current per the provider's own
docs at the time this was last verified, not "broken" — deprecated entries
stay selectable for testing/comparison, just flagged so the frontend can
visually de-emphasize them. Provider availability shifts; re-verify against
Anthropic's and DeepSeek's docs before trusting this blindly.
"""

MODEL_REGISTRY = {
    "anthropic": [
        {"id": "claude-sonnet-4-5", "label": "Claude Sonnet 4.5", "supports_effort": True, "deprecated": True},
        {"id": "claude-sonnet-5", "label": "Claude Sonnet 5", "supports_effort": True, "deprecated": False},
        {"id": "claude-opus-4-8", "label": "Claude Opus 4.8", "supports_effort": True, "deprecated": False},
    ],
    "deepseek": [
        {"id": "deepseek-v4-flash", "label": "DeepSeek V4 Flash", "supports_effort": True, "deprecated": False},
        {"id": "deepseek-v4-pro", "label": "DeepSeek V4 Pro", "supports_effort": True, "deprecated": False},
        {"id": "deepseek-chat", "label": "DeepSeek Chat (legacy)", "supports_effort": False, "deprecated": True},
    ],
}

EFFORT_LEVELS = ["low", "medium", "high"]


def default_model(provider: str) -> str:
    """First non-deprecated entry for the provider, used when a request omits model."""
    for entry in MODEL_REGISTRY[provider]:
        if not entry["deprecated"]:
            return entry["id"]
    return MODEL_REGISTRY[provider][0]["id"]


def model_supports_effort(provider: str, model_id: str) -> bool:
    for entry in MODEL_REGISTRY.get(provider, []):
        if entry["id"] == model_id:
            return entry["supports_effort"]
    return False
