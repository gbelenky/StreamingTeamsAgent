"""Entry point: `uv run streaming-teams-agent` or `python -m streaming_teams_agent`."""

from __future__ import annotations

import logging
import os
from os import path

from dotenv import load_dotenv

from .agent import build_agent_app
from .server import serve


def _configure_observability() -> None:
    conn = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not conn:
        return
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(connection_string=conn)
    except Exception:  # noqa: BLE001
        logging.getLogger(__name__).warning(
            "Failed to configure Azure Monitor OpenTelemetry", exc_info=True
        )


def main() -> None:
    load_dotenv(path.join(path.dirname(path.dirname(path.dirname(__file__))), ".env"))
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
    _configure_observability()

    agent_app, connection_manager = build_agent_app()
    serve(
        agent_application=agent_app,
        auth_configuration=connection_manager.get_default_connection_configuration(),
    )


if __name__ == "__main__":
    main()
