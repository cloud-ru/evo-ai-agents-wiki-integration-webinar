from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    Task,
    TaskState,
    UnsupportedOperationError,
)
from a2a.utils import (
    new_agent_text_message,
    new_task,
)
from a2a.utils.errors import ServerError
from .a2a_agent import A2Aagent
from .logging_utils import get_logger


logger = get_logger(__name__)


class MyAgentExecutor(AgentExecutor):
    """AgentExecutor implementation for our Wiki agent."""

    def __init__(self):
        logger.info("Initializing MyAgentExecutor")
        self.agent = A2Aagent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        query = context.get_user_input()
        logger.info(
            "execute called; context_id=%s", getattr(context, "context_id", None)
        )
        task = context.current_task

        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
            logger.info("Created new task; task_id=%s", task.id)
        updater = TaskUpdater(event_queue, task.id, task.context_id)

        async for item in self.agent.stream(query, task.context_id):
            is_task_complete = item["is_task_complete"]
            require_user_input = item["require_user_input"]
            is_error = item["is_error"]
            is_event = item["is_event"]

            if is_error:
                logger.error("Stream item indicated error; task_id=%s", task.id)
                await updater.update_status(
                    TaskState.failed,
                    new_agent_text_message(item["content"], task.context_id, task.id),
                )
                break
            if is_event:
                logger.info("Stream event; task_id=%s", task.id)
                await updater.update_status(
                    TaskState.working,
                    new_agent_text_message(item["content"], task.context_id, task.id),
                )
                continue
            if not is_task_complete and not require_user_input:
                logger.info("Working update; task_id=%s", task.id)
                await updater.update_status(
                    TaskState.working,
                    new_agent_text_message(item["content"], task.context_id, task.id),
                )
                continue

            if not is_task_complete and require_user_input:
                logger.info("Input required; task_id=%s", task.id)
                await updater.update_status(
                    TaskState.input_required,
                    new_agent_text_message(item["content"], task.context_id, task.id),
                )
                break
            if is_task_complete and not require_user_input:
                logger.info("Task completed; task_id=%s", task.id)
                await updater.update_status(
                    TaskState.completed,
                    new_agent_text_message(item["content"], task.context_id, task.id),
                )
                break

    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        raise ServerError(error=UnsupportedOperationError())
