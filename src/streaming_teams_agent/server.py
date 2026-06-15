"""aiohttp server hosting the agent on /api/messages."""

from __future__ import annotations

import os

from aiohttp.web import Application, Request, Response, run_app
from microsoft_agents.hosting.aiohttp import (
    jwt_authorization_middleware,
    start_agent_process,
)


def build_app(agent_application, auth_configuration) -> Application:
    async def messages(req: Request) -> Response:
        agent = req.app["agent_app"]
        adapter = req.app["adapter"]
        return await start_agent_process(req, agent, adapter)

    async def health(_req: Request) -> Response:
        return Response(status=200, text="ok")

    app = Application(middlewares=[jwt_authorization_middleware])
    app.router.add_post("/api/messages", messages)
    app.router.add_get("/api/messages", lambda _: Response(status=200))
    app.router.add_get("/healthz", health)

    app["agent_configuration"] = auth_configuration
    app["agent_app"] = agent_application
    app["adapter"] = agent_application.adapter
    return app


def serve(agent_application, auth_configuration) -> None:
    app = build_app(agent_application, auth_configuration)
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "3978"))
    run_app(app, host=host, port=port)
