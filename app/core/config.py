from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    DATABASE_URL_DIRECT: str
    ANTHROPIC_API_KEY: str
    DEEPSEEK_API_KEY: str
    LLM_PROVIDER: str = "deepseek"
    FRONTEND_ORIGIN: str = "http://localhost:3000"

    @field_validator("DATABASE_URL")
    @classmethod
    def _normalize_runtime_url(cls, v: str) -> str:
        # asyncpg doesn't parse sslmode/channel_binding from the URL; ssl is passed via
        # connect_args instead. Also normalize the scheme in case a raw Neon URL (postgresql://)
        # was pasted in instead of the postgresql+asyncpg:// form the async engine needs.
        v = v.split("?")[0]
        if v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


settings = Settings()
