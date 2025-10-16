from __future__ import annotations
import os
import logging

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool import SseConnectionParams, McpToolset
from .logging_utils import get_logger


logger = get_logger(__name__)


llm_model = LiteLlm(
    model=os.getenv("LLM_MODEL"),
    api_base=os.getenv("LLM_API_BASE"),
    api_key=os.getenv("LLM_API_KEY"),
)


def _parse_mcp_urls(raw_urls: str | None) -> list[str]:
    if not raw_urls:
        return []
    return [u.strip() for u in raw_urls.split(",") if u.strip()]


_mcp_urls = _parse_mcp_urls(os.getenv("MCP_URL"))
logger.info("agent.py configuring worker_agent; mcp_urls=%s", _mcp_urls)

worker_agent = Agent(
    model=llm_model,
    name=os.getenv("AGENT_NAME", "Wiki_Agent").replace(" ", "_"),
    description=os.getenv(
        "AGENT_DESCRIPTION", "Answers questions via corporate wiki using MCP"
    ),
    instruction=os.getenv("AGENT_SYSTEM_PROMPT"),
    tools=[
        McpToolset(connection_params=SseConnectionParams(url=url)) for url in _mcp_urls
    ],
)
logger.info("worker_agent initialized; name=%s", os.getenv("AGENT_NAME", "Wiki_Agent"))

root_agent = worker_agent
