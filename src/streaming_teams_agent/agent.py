"""Simple streaming agent for Microsoft Teams.

Streams answers about human history from a Microsoft Foundry chat model
back to the Teams client using the M365 Agents SDK streaming surface.
"""

from __future__ import annotations

import asyncio
import logging
import sys
import traceback
from os import environ

from microsoft_agents.activity import (
    ActivityTypes,
    SensitivityUsageInfo,
    load_configuration_from_env,
)
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import (
    AgentApplication,
    Authorization,
    MemoryStorage,
    TurnContext,
    TurnState,
)

from .foundry_client import get_model_deployment_name, get_openai_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a friendly history tutor. Answer the user's question about "
    "human history accurately and engagingly. Keep answers under 300 words "
    "unless the user asks for more detail."
)


def build_agent_app() -> tuple[AgentApplication[TurnState], MsalConnectionManager]:
    """Wire up storage, auth, adapter, and AgentApplication."""
    agents_sdk_config = load_configuration_from_env(environ)

    storage = MemoryStorage()
    connection_manager = MsalConnectionManager(**agents_sdk_config)
    adapter = CloudAdapter(connection_manager=connection_manager)
    authorization = Authorization(storage, connection_manager, **agents_sdk_config)

    agent_app = AgentApplication[TurnState](
        storage=storage,
        adapter=adapter,
        authorization=authorization,
        **agents_sdk_config,
    )

    _register_handlers(agent_app)
    return agent_app, connection_manager


def _register_handlers(agent_app: AgentApplication[TurnState]) -> None:
    @agent_app.conversation_update("membersAdded")
    async def on_members_added(context: TurnContext, _state: TurnState):
        await context.send_activity(
            "👋 Hi! I'm a streaming history tutor. "
            "Ask me anything about human history — answers stream in real time."
        )
        return True

    @agent_app.activity(ActivityTypes.invoke)
    async def on_invoke(context: TurnContext, _state: TurnState):
        from microsoft_agents.activity import Activity

        await context.send_activity(
            Activity(type=ActivityTypes.invoke_response, value={"status": 200})
        )

    @agent_app.activity("message")
    async def on_message(context: TurnContext, _state: TurnState):
        user_text = (context.activity.text or "").strip()
        if not user_text:
            await context.send_activity("Please send a question about human history.")
            return

        stream = context.streaming_response
        stream.set_generated_by_ai_label(True)
        stream.set_feedback_loop(True)
        stream.set_sensitivity_label(
            SensitivityUsageInfo(
                type="https://schema.org/Message",
                schema_type="CreativeWork",
                name="General",
            )
        )

        # SDK Teams default is `_interval = 1.0` second, which (combined with
        # the SDK's _chunk_queued dedupe) makes a fast model look like only
        # 2-3 visible chunks on a short answer. The interval is actually a
        # `await asyncio.sleep(_interval)` AFTER each `typing` activity is
        # sent — all tokens that arrive during that sleep are coalesced into
        # the next single update. Lowering to ~0.15s yields ~6 updates/sec
        # which gives a noticeably smoother streaming UX without tripping
        # the Teams Bot Connector per-stream rate limit.
        stream_interval_s = float(environ.get("STREAM_INTERVAL_SECONDS", "0.15"))
        stream._interval = stream_interval_s  # noqa: SLF001 — SDK exposes no setter

        stream.queue_informative_update("Consulting the history books…")

        try:
            client = get_openai_client()
            model = get_model_deployment_name()

            response = await client.chat.completions.create(
                model=model,
                stream=True,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_text},
                ],
            )

            async for chunk in response:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                token = getattr(delta, "content", None)
                if token:
                    stream.queue_text_chunk(token)
                    # Pace the producer slightly below the SDK flush interval so
                    # the typing-activity coalescer never builds up a large
                    # backlog. Without this, a fast model can emit 50+ tokens
                    # during a single _interval window, which all collapse into
                    # one visible chunk.
                    await asyncio.sleep(0)
        except Exception:  # noqa: BLE001
            logger.exception("Foundry streaming call failed")
            stream.queue_text_chunk(
                "\n\n_(Sorry — I hit an error while streaming the answer.)_"
            )
        finally:
            # Let the SDK flush any tokens queued in the last _interval
            # window BEFORE end_stream() fires. Otherwise end_stream()'s
            # final "message" activity (which contains the full accumulated
            # text) replaces the streaming bubble in one big jump, hiding
            # the last batch of tokens behind a single update.
            try:
                await stream.wait_for_queue()
            except Exception:  # noqa: BLE001
                logger.exception("wait_for_queue failed; proceeding to end_stream")
            await stream.end_stream()

    @agent_app.error
    async def on_error(context: TurnContext, error: Exception):
        print(f"\n[on_turn_error] unhandled error: {error}", file=sys.stderr)
        traceback.print_exc()
        try:
            await context.send_activity("The agent encountered an error.")
        except Exception:  # noqa: BLE001
            logger.exception("Failed to send error message to user")
