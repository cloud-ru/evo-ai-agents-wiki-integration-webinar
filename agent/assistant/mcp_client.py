import json
import logging
import asyncio
from typing import Any, Dict
from .logging_utils import get_logger

# Official MCP client (SSE transport)
_mcp_import_error = None
try:
    from mcp import ClientSession
    from mcp.client.sse import sse_client
except ImportError as _e:
    _mcp_import_error = _e
    ClientSession = None
    sse_client = None

logger = get_logger(__name__)


class McpSearchClient:
    """
    Client for communicating with the MCP search server using official MCP Python client over SSE.
    """

    def __init__(self, mcp_server_url: str):
        """
        Initialize the MCP client.

        Args:
            mcp_server_url (str): The URL of the MCP server
        """
        base = mcp_server_url.rstrip("/")
        if not base.endswith("/sse"):
            base = f"{base}/sse"
        self.sse_url = base

    def _normalize_content(self, raw_content: Any) -> Dict[str, Any]:
        """
        Normalize various possible MCP content representations into a consistent
        structure of the form: {"content": [{"type": "text", "text": "..."}, ...]}

        The official MCP client may return pydantic models (e.g., TextContent),
        dictionaries, or other objects. This method converts all of them into
        plain dictionaries expected by downstream code.
        """
        normalized_items = []

        if raw_content is None:
            return {"content": []}

        items = raw_content if isinstance(raw_content, (list, tuple)) else [raw_content]

        for item in items:
            # Already a plain dict
            if isinstance(item, dict):
                # Ensure required keys; fall back to string conversion if missing
                item_type = item.get("type")
                item_text = item.get("text")
                if item_type is None and item_text is None:
                    normalized_items.append({"type": "text", "text": str(item)})
                else:
                    normalized_items.append(
                        {
                            "type": item_type or "text",
                            "text": item_text or "",
                        }
                    )
                continue

            # pydantic v2 model objects expose model_dump
            try:
                model_dump = getattr(item, "model_dump", None)
                if callable(model_dump):
                    dumped = model_dump()
                    normalized_items.append(
                        {
                            "type": dumped.get("type", "text"),
                            "text": dumped.get("text", ""),
                        }
                    )
                    continue
            except Exception:
                pass

            # Fallback: duck-typed attributes (e.g., TextContent with .type/.text)
            item_type = getattr(item, "type", None)
            item_text = getattr(item, "text", None)
            if item_type is not None or item_text is not None:
                normalized_items.append(
                    {
                        "type": item_type or "text",
                        "text": item_text or "",
                    }
                )
                continue

            # Last resort: stringify unknown objects
            normalized_items.append({"type": "text", "text": str(item)})

        return {"content": normalized_items}

    async def search(self, query: str) -> Dict[str, Any]:
        """
        Search for content using the MCP server via MCP SSE transport.

        Args:
            query (str): The search query

        Returns:
            Dict[str, Any]: The search results from the MCP server
        """
        try:
            logger.info(f"🔍 Searching MCP server with query: '{query}'")

            if ClientSession is None or sse_client is None:
                details = f" ({_mcp_import_error})" if _mcp_import_error else ""
                raise RuntimeError(
                    "Official MCP client not available. Ensure it's installed and compatible: "
                    "pip install -U 'mcp>=1.17.0'" + details
                )

            # Use sse_client as context manager to get streams
            async with sse_client(url=self.sse_url) as streams:
                # Create ClientSession with the streams
                async with ClientSession(*streams) as session:
                    # Initialize the session
                    await session.initialize()

                    # Call the search tool
                    result = await session.call_tool("search", {"query": query})

                    # Handle different response formats
                    if hasattr(result, "content"):
                        # Result is a CallToolResult object with content attribute
                        logger.info("✅ MCP search completed successfully")
                        return self._normalize_content(result.content)
                    elif isinstance(result, dict) and "content" in result:
                        logger.info("✅ MCP search completed successfully")
                        return self._normalize_content(result.get("content"))
                    else:
                        logger.warning("⚠️ Unexpected MCP response format")
                        return {
                            "content": [{"type": "text", "text": "No results found"}]
                        }

        except asyncio.TimeoutError:
            logger.error("❌ MCP server request timed out")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Search request timed out. Please try again.",
                    }
                ]
            }
        except Exception as e:
            logger.exception("❌ MCP client error")
            return {"content": [{"type": "text", "text": f"Search failed: {str(e)}"}]}

    async def close(self):
        """Close the HTTP client."""
        # Official client uses per-call context managers; nothing persistent to close
        return
