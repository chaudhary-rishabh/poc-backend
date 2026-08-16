from pydantic import BaseModel


class TechStack(BaseModel):
    frontend: str
    backend: str
    database: str


class DbField(BaseModel):
    name: str
    type: str


class DbTable(BaseModel):
    table: str
    fields: list[DbField]


class ApiRoute(BaseModel):
    method: str
    path: str
    purpose: str


class DocC(BaseModel):
    tech_stack: TechStack
    db_schema: list[DbTable]
    api_routes: list[ApiRoute]
    folder_structure: str
