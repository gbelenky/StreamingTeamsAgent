"""Microsoft Foundry client wrapper.

Uses the classic Azure OpenAI inference surface
(`/openai/deployments/{name}/chat/completions?api-version=...`) against the
underlying AI Services resource of a Microsoft Foundry project, with
DefaultAzureCredential (Managed Identity in Azure, `az login` locally).

We bypass `AIProjectClient.get_openai_client()` because some Foundry projects
do not yet support its newer `/openai/v1/` routing surface and respond with
404 DeploymentNotFound; the classic deployment-name path works everywhere.
"""

from __future__ import annotations

import os
from functools import lru_cache

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI

_COGNITIVE_SERVICES_SCOPE = "https://cognitiveservices.azure.com/.default"
_DEFAULT_API_VERSION = "2024-10-21"


@lru_cache(maxsize=1)
def _credential() -> DefaultAzureCredential:
    return DefaultAzureCredential(exclude_interactive_browser_credential=False)


def _resource_endpoint() -> str:
    raw = os.environ.get("FOUNDRY_PROJECT_ENDPOINT")
    if not raw:
        raise RuntimeError(
            "FOUNDRY_PROJECT_ENDPOINT is not set. "
            "Set it to your Microsoft Foundry project endpoint, e.g. "
            "https://<your-project>.services.ai.azure.com/api/projects/<your-project>"
        )
    # Strip the /api/projects/<name> suffix to get the AI Services resource root,
    # which is what the Azure OpenAI inference surface needs.
    marker = "/api/projects/"
    idx = raw.find(marker)
    return raw[:idx] if idx >= 0 else raw.rstrip("/")


@lru_cache(maxsize=1)
def get_openai_client() -> AsyncAzureOpenAI:
    """Return an async Azure OpenAI client bound to the Foundry project's resource.

    Async is critical for streaming: a sync client's `for chunk in response:`
    blocks the asyncio event loop, preventing the M365 Agents SDK background
    coroutine from flushing intermediate `typing` activities to Teams. Result
    would be that all tokens arrive in a single final message instead of
    streaming progressively.
    """
    token_provider = get_bearer_token_provider(
        _credential(), _COGNITIVE_SERVICES_SCOPE
    )
    return AsyncAzureOpenAI(
        azure_endpoint=_resource_endpoint(),
        azure_ad_token_provider=token_provider,
        api_version=os.environ.get("FOUNDRY_API_VERSION", _DEFAULT_API_VERSION),
    )


def get_model_deployment_name() -> str:
    name = os.environ.get("FOUNDRY_MODEL_DEPLOYMENT")
    if not name:
        raise RuntimeError(
            "FOUNDRY_MODEL_DEPLOYMENT is not set. "
            "Set it to the name of a chat model deployment in your Foundry project."
        )
    return name
