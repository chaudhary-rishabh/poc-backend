from pydantic import BaseModel


class Role(BaseModel):
    name: str
    description: str


class Screen(BaseModel):
    name: str
    purpose: str
    key_elements: list[str]
    visible_to_roles: list[str] = []


class DocB(BaseModel):
    roles: list[Role]
    screens: list[Screen]
    flow: list[str]
    features: list[str]
