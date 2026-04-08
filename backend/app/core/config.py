from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    app_env: str = "development"
    log_level: str = "INFO"

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://orgagent:changeme@localhost:5432/orgagent"
    readonly_db_url: str = ""
    whitelisted_tables: str = "users,projects,tickets,departments"

    # Keycloak
    keycloak_url: str = "http://keycloak:8080"
    keycloak_realm: str = "org-agent"
    keycloak_client_id: str = "org-agent-backend"
    keycloak_client_secret: str = ""
    keycloak_audience: str = "org-agent-backend"

    # LLM provider — "anthropic" or "openai"
    llm_provider: str = "anthropic"

    # Anthropic
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-5"

    # OpenAI (LLM — separate from embedding key below)
    openai_llm_api_key: str = ""
    openai_model: str = "gpt-4o"

    # pgvector / RAG
    embedding_provider: str = "openai"
    openai_api_key: str = ""
    rag_top_k: int = 8
    rag_hybrid_alpha: float = 0.75   # weight for semantic score (1-alpha = BM25/FTS weight)

    # Jira
    jira_base_url: str = ""
    jira_service_account_email: str = ""
    jira_api_token: str = ""
    jira_cache_ttl_seconds: int = 60

    # Redis / Cache
    redis_url: str = "redis://redis:6379/0"
    cache_enabled: bool = False

    @property
    def whitelisted_tables_set(self) -> set[str]:
        return {t.strip() for t in self.whitelisted_tables.split(",") if t.strip()}

    @property
    def keycloak_oidc_config_url(self) -> str:
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}/.well-known/openid-configuration"


@lru_cache
def get_settings() -> Settings:
    return Settings()
