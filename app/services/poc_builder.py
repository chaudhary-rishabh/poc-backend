import json
from pathlib import Path

from app.schemas.doc_b import DocB

_SKELETON_PATH = Path(__file__).resolve().parent.parent / "templates" / "poc_skeleton.html"


def build_poc_html(doc_b: DocB, app_title: str = "POC Mockup") -> str:
    skeleton = _SKELETON_PATH.read_text(encoding="utf-8")

    roles = [r.model_dump() for r in doc_b.roles]
    screens = [s.model_dump() for s in doc_b.screens]
    features = list(doc_b.features)

    html = (
        skeleton.replace("__APP_TITLE__", app_title)
        .replace("__ROLES_JSON__", json.dumps(roles))
        .replace("__SCREENS_JSON__", json.dumps(screens))
        .replace("__FEATURES_JSON__", json.dumps(features))
    )

    if "ReactDOM.createRoot" not in html or "__ROLES_JSON__" in html:
        raise ValueError("POC template fill failed validation: skeleton markers not fully replaced.")

    return html
