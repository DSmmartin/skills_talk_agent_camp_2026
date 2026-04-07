"""
agent/setup.py

Call setup_openai() once at process start (before importing any agent module)
to configure the OpenAI client, MLflow autologging, and disable the built-in
agents tracing (MLflow handles it instead).
"""

import mlflow
from agents import (
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)

from agentic_system.config import settings


def setup_openai() -> None:
    """Configure the OpenAI Agents SDK client and enable MLflow OpenAI autologging.

    Reads OPENAI_PROVIDER from the environment:
    - "azure"  → AsyncAzureOpenAI with endpoint + key + api_version from env.
    - "openai" → AsyncOpenAI with OPENAI_API_KEY from env.

    In both cases:
    - mlflow.openai.autolog() captures every LLM call as an MLflow trace.
    - set_tracing_disabled(True) turns off the built-in agents SDK tracing
      so only MLflow tracing is active.
    """
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(settings.mlflow_experiment_name)
    mlflow.openai.autolog()

    if settings.openai_provider == "azure":
        from openai import AsyncAzureOpenAI
        from agentic_system.models import AzureOpenAICredentials

        creds = AzureOpenAICredentials.from_env()
        client = AsyncAzureOpenAI(
            azure_endpoint=creds.azure_endpoint,
            api_key=creds.api_key,
            api_version=creds.api_version,
        )
        set_default_openai_client(client=client)
        set_default_openai_api("chat_completions")

    else:
        from openai import AsyncOpenAI
        from agentic_system.models import OpenAICredentials

        creds = OpenAICredentials.from_env()
        client = AsyncOpenAI(api_key=creds.api_key)
        set_default_openai_client(client=client)
        set_default_openai_api("chat_completions")

    set_tracing_disabled(disabled=True)
