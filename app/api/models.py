from fastapi import APIRouter

from app.core.model_registry import EFFORT_LEVELS, MODEL_REGISTRY

router = APIRouter()


@router.get("/models")
async def list_models():
    return {"models": MODEL_REGISTRY, "effort_levels": EFFORT_LEVELS}
