"""Microsoft Foundry client wrapper.

Uses azure-ai-projects (GA) + DefaultAzureCredential (Managed Identity in
Azure, az login locally) to obtain a streaming chat client from your
Foundry project.
"""

from __future__ import annotations

import os
from functools import lru_cache

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential


@lru_cache(maxsize=1)
def _credential() -> DefaultAzureCredential:
    return DefaultAzureCredential(exclude_interactive_browser_credential=False)


@lru_cache(maxsize=1)
def _project_client() -> AIProjectClient:
    endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT")
    if not endpoint:
        raise RuntimeError(
            "FOUNDRY_PROJECT_ENDPOINT is not set. "
            "Set it to your Microsoft Foundry project endpoint, e.g. "
            "https://<your-project>.services.ai.azure.com/api/projects/<your-project>"
        )
    return AIProjectClient(endpoint=endpoint, credential=_credential())


def get_openai_client():
    """Return an OpenAI-compatible client bound to your Foundry project.

    The Foundry project handles auth, model routing, content safety,
    and telemetry.
    """
    return _project_client().get_openai_client()


def get_model_deployment_name() -> str:
    name = os.environ.get("FOUNDRY_MODEL_DEPLOYMENT")
    if not name:
        raise RuntimeError(
            "FOUNDRY_MODEL_DEPLOYMENT is not set. "
            "Set it to the name of a chat model deployment in your Foundry project."
        )
    return name
