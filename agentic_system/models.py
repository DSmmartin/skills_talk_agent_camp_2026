from pydantic import BaseModel


# ── OpenAI credentials ────────────────────────────────────────────────────────

class AzureOpenAICredentials(BaseModel):
    """Azure OpenAI credentials loaded from environment variables."""

    azure_endpoint: str
    api_key: str
    api_version: str
    deployment: str

    @classmethod
    def from_env(cls) -> "AzureOpenAICredentials":
        from agentic_system.config import settings
        return cls(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            deployment=settings.azure_openai_deployment,
        )


class OpenAICredentials(BaseModel):
    """Default OpenAI credentials loaded from environment variables."""

    api_key: str

    @classmethod
    def from_env(cls) -> "OpenAICredentials":
        from agentic_system.config import settings
        return cls(api_key=settings.openai_api_key)

