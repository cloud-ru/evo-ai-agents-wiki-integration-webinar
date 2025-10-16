from typing import Dict, Any, AsyncGenerator
import asyncio
import logging
import os

from .wiki_assistant import WikiAssistant
from .logging_utils import get_logger


logger = get_logger(__name__)


class A2Aagent:
    def __init__(self):
        # Keep a single assistant instance to reuse connections and prompts
        mcp_urls = [
            u.strip()
            for u in os.environ.get("MCP_URL", "http://localhost:3001").split(",")
            if u.strip()
        ]
        # Use the first URL, matching legacy behavior
        self.mcp_server_url = mcp_urls[0]
        logger.info("Initializing A2Aagent; mcp_server_url=%s", self.mcp_server_url)
        self.assistant = WikiAssistant(mcp_server_url=self.mcp_server_url)

    async def invoke(self, query: str, session_id: str) -> Dict[str, Any]:
        # Synchronous underlying call wrapped for API symmetry
        logger.info(
            "invoke called; session_id=%s query_len=%d",
            session_id,
            len(query) if query else 0,
        )
        answer = await self.assistant.answer(query)
        logger.info("invoke completed; answer_len=%d", len(answer) if answer else 0)
        return {
            "is_task_complete": True,
            "require_user_input": False,
            "content": answer,
            "is_error": False,
            "is_event": False,
        }

    async def stream(
        self, query: str, session_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        # Emit a short progress event similar to example, then final answer
        logger.info(
            "stream called; session_id=%s query_len=%d",
            session_id,
            len(query) if query else 0,
        )
        yield {
            "is_task_complete": False,
            "require_user_input": False,
            "content": "Searching corporate wiki...",
            "is_error": False,
            "is_event": True,
        }

        answer = await self.assistant.answer(query)

        yield {
            "is_task_complete": True,
            "require_user_input": False,
            "content": answer,
            "is_error": False,
            "is_event": False,
        }

    def sync_invoke(self, query: str, session_id: str) -> Dict[str, Any]:
        logger.info("sync_invoke called; session_id=%s", session_id)
        return asyncio.run(self.invoke(query, session_id))

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
