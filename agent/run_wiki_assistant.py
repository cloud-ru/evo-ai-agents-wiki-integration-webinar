#!/usr/bin/env python3
import os
import sys
import asyncio
import argparse

from dotenv import load_dotenv

from assistant.wiki_assistant import WikiAssistant


async def run_once(question: str) -> int:
    load_dotenv()

    # MCP_URL supports comma-separated SSE URLs (env.example)
    mcp_urls = [
        u.strip()
        for u in os.environ.get("MCP_URL", "http://localhost:3001").split(",")
        if u.strip()
    ]
    mcp_url = mcp_urls[0] if mcp_urls else ""
    if not mcp_url:
        print("❌ MCP_URL is not set in .env")
        return 2

    assistant = WikiAssistant(mcp_url)
    try:
        answer = await assistant.answer(question)
        print("\n=== Answer ===\n")
        print(answer or "<empty>")
        print("\n==============\n")
        return 0
    finally:
        await assistant.close()


async def run_repl() -> int:
    load_dotenv()

    # MCP_URL supports comma-separated SSE URLs (env.example)
    mcp_urls = [
        u.strip()
        for u in os.environ.get("MCP_URL", "http://localhost:3001").split(",")
        if u.strip()
    ]
    # Use the first URL, matching simple local run behavior
    mcp_url = mcp_urls[0] if mcp_urls else ""
    if not mcp_url:
        print("❌ MCP_URL is not set in .env")
        return 2

    assistant = WikiAssistant(mcp_url)
    try:
        print("Corporate Wiki Assistant (type 'exit' to quit)\n")
        while True:
            try:
                question = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not question or question.lower() in {"exit", "quit"}:
                break

            try:
                answer = await assistant.answer(question)
                print(f"Assistant: {answer}\n")
            except Exception as e:
                print(f"❌ Error: {e}\n")
        return 0
    finally:
        await assistant.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run WikiAssistant locally with .env settings"
    )
    parser.add_argument("--question", "-q", type=str, help="Single question to ask")
    args = parser.parse_args()

    if args.question:
        return asyncio.run(run_once(args.question))
    return asyncio.run(run_repl())


if __name__ == "__main__":
    sys.exit(main())
