from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPOSITORY_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_cors_origins: Annotated[list[str], NoDecode] = Field(
        default=["http://localhost:3000"],
        alias="API_CORS_ORIGINS",
    )
    default_chat_top_k: int = Field(default=5, alias="DEFAULT_CHAT_TOP_K")
    default_chat_temperature: float = Field(default=0.1, alias="DEFAULT_CHAT_TEMPERATURE")
    max_history_messages: int = Field(default=8, alias="MAX_HISTORY_MESSAGES")
    indexer_batch_size: int = Field(default=24, alias="INDEXER_BATCH_SIZE")
    knowledge_base_path: str = Field(
        default=str(REPOSITORY_ROOT / "data" / "knowledge_base"),
        alias="KNOWLEDGE_BASE_PATH",
    )
    hr_database_path: str = Field(
        default=str(REPOSITORY_ROOT / "data" / "hr.sqlite3"),
        alias="HR_DATABASE_PATH",
    )
    openai_agents_enabled: bool = Field(default=False, alias="OPENAI_AGENTS_ENABLED")
    agent_memory_path: str = Field(
        default=str(REPOSITORY_ROOT / "data" / "agent_memory.sqlite3"),
        alias="AGENT_MEMORY_PATH",
    )
    sql_max_rows: int = Field(default=25, alias="SQL_MAX_ROWS")
    mock_azure_mode: bool = Field(default=False, alias="MOCK_AZURE_MODE")

    azure_openai_endpoint: str | None = Field(default=None, alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str | None = Field(default=None, alias="AZURE_OPENAI_API_KEY")
    azure_openai_chat_deployment: str | None = Field(default=None, alias="AZURE_OPENAI_CHAT_DEPLOYMENT")
    azure_openai_embedding_deployment: str | None = Field(
        default=None,
        alias="AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
    )

    azure_search_endpoint: str | None = Field(default=None, alias="AZURE_SEARCH_ENDPOINT")
    azure_search_api_key: str | None = Field(default=None, alias="AZURE_SEARCH_API_KEY")
    azure_search_index_name: str = Field(default="hr-policy-index", alias="AZURE_SEARCH_INDEX_NAME")

    @field_validator("api_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def azure_enabled(self) -> bool:
        required = [
            self.azure_openai_endpoint,
            self.azure_openai_api_key,
            self.azure_openai_chat_deployment,
            self.azure_openai_embedding_deployment,
            self.azure_search_endpoint,
            self.azure_search_api_key,
            self.azure_search_index_name,
        ]
        return all(required) and not self.mock_azure_mode


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
