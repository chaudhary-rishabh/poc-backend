from pydantic import BaseModel, Field


class DocA(BaseModel):
    goal: str
    current_process: str
    pain_points: list[str]
    missing_info: list[str] = Field(
        description="Distinct from pain_points; must flag anything ambiguous or absent in the input."
    )
    proposed_process: str
