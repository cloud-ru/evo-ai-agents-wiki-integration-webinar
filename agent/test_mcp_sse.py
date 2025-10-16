#!/usr/bin/env python3
"""
Simple test script to verify MCP client SSE functionality.
"""
import asyncio
import os
from assistant.mcp_client import McpSearchClient


async def test_mcp_sse():
    """Test the MCP client with SSE."""
    # Get MCP server URL from environment or use the one from the logs
    mcp_url = os.getenv(
        "MCP_SERVER_URL",
        "https://d68d25dd-a268-4383-bef5-9ffa7f31a9e7-mcp-server.ai-agent.inference.cloud.ru",
    )

    print(f"Testing MCP client with URL: {mcp_url}")

    client = McpSearchClient(mcp_url)

    try:
        # Test search
        result = await client.search("test query")
        print(f"Search result: {result}")

        if "content" in result:
            print("✅ MCP client is working correctly")
        else:
            print("⚠️ Unexpected result format")

    except Exception as e:
        print(f"❌ Error testing MCP client: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_mcp_sse())
