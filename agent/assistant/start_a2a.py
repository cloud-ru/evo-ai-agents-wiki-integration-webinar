import os

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
)
from dotenv import load_dotenv
from .logging_utils import get_logger, set_global_log_level

from .agent_task_manager import MyAgentExecutor

try:
    from phoenix.otel import register  # type: ignore
except Exception:  # pragma: no cover - optional dependency

    def register(*args, **kwargs):  # type: ignore
        return None


import logging


load_dotenv()
set_global_log_level(os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger(__name__)


def main():
    try:
        logger.info("Starting A2A application")
        if os.getenv("ENABLE_PHOENIX", "false").lower() == "true":
            register(
                project_name=os.getenv("AGENT_NAME"),
                endpoint=os.getenv("PHOENIX_ENDPOINT"),
                auto_instrument=True,
            )

        capabilities = AgentCapabilities(streaming=True)
        my_agent_executor = MyAgentExecutor()
        agent_card = AgentCard(
            name=os.getenv("AGENT_NAME", "Wiki Agent"),
            description=os.getenv(
                "AGENT_DESCRIPTION", "Answers questions via corporate wiki using MCP"
            ),
            url=os.getenv("URL_AGENT"),
            version=os.getenv("AGENT_VERSION", "1.0.0"),
            default_input_modes=my_agent_executor.agent.SUPPORTED_CONTENT_TYPES,
            default_output_modes=my_agent_executor.agent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[],
        )
        logger.info(
            "Agent card created; name=%s version=%s",
            agent_card.name,
            agent_card.version,
        )
        request_handler = DefaultRequestHandler(
            agent_executor=my_agent_executor,
            task_store=InMemoryTaskStore(),
        )
        server = A2AStarletteApplication(
            agent_card=agent_card, http_handler=request_handler
        )
        import uvicorn

        port = int(os.getenv("PORT", 10000))
        logger.info("Starting uvicorn on port %d", port)
        uvicorn.run(server.build(), host="0.0.0.0", port=port)
    except Exception as e:
        logger.exception("An error occurred during server startup")
        exit(1)


if __name__ == "__main__":
    main()
