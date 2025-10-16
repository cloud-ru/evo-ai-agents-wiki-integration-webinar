import asyncio
import logging
from dataclasses import dataclass
from typing import List

from .mcp_client import McpSearchClient
from .logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievedDocument:
    page_content: str
    metadata: dict


class McpKeywordEnhancedRetriever:
    """Keyword-enhanced retriever without LangChain.

    Expects a callable `keyword_fn(question: str) -> str` that returns comma-separated keywords.
    """

    def __init__(self, mcp_client: McpSearchClient, keyword_fn):
        self.mcp_client = mcp_client
        self.keyword_fn = keyword_fn

    async def invoke(self, query: str) -> List[RetrievedDocument]:
        return await self._ainvoke(query)

    async def _ainvoke(self, query: str) -> List[RetrievedDocument]:
        logger.info(f"🤔 Original question: '{query}'")

        try:
            extracted_keywords = self.keyword_fn(query).strip()
            logger.info(f"🔑 Extracted keywords: '{extracted_keywords}'")

            mcp_result = await self.mcp_client.search(extracted_keywords)
            documents = self._parse_mcp_response(mcp_result)
            logger.info(f"📄 MCP server returned {len(documents)} documents")
            return documents

        except Exception as e:
            logger.exception("❌ Error in keyword extraction or MCP search")
            logger.info(f"🔄 Falling back to original query: '{query}'")
            try:
                mcp_result = await self.mcp_client.search(query)
                documents = self._parse_mcp_response(mcp_result)
                return documents
            except Exception as fallback_error:
                logger.exception("❌ Fallback search also failed")
                return []

    def _parse_mcp_response(self, mcp_result: dict) -> List[RetrievedDocument]:
        documents: List[RetrievedDocument] = []

        try:
            if "content" in mcp_result and mcp_result["content"]:
                for content_item in mcp_result["content"]:
                    if content_item.get("type") == "text":
                        text = content_item.get("text", "")
                        if (
                            text
                            and not text.startswith("No results found")
                            and not text.startswith("Search failed")
                        ):
                            documents.append(
                                RetrievedDocument(
                                    page_content=text,
                                    metadata={
                                        "source": "mcp_search",
                                        "query": "search_result",
                                    },
                                )
                            )

            return documents

        except Exception as e:
            logger.exception("❌ Error parsing MCP response")
            return []
