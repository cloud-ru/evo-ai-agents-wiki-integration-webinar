import logging
import os

from dotenv import load_dotenv
from litellm import completion

from .mcp_client import McpSearchClient
from .prompts import KEYWORD_EXTRACTION_TEMPLATE, QA_TEMPLATE
from .retrievers import McpKeywordEnhancedRetriever, RetrievedDocument
from .logging_utils import get_logger

logger = get_logger(__name__)


class WikiAssistant:
    """
    A corporate wiki assistant that uses MCP server for document retrieval and LLM for answering questions.
    """

    def __init__(self, mcp_server_url: str):
        """
        Initialize the assistant with all necessary components.

        Args:
            mcp_server_url (str): The URL of the MCP server
        """
        self._mcp_server_url = mcp_server_url

        self._load_environment()
        logger.info("Initializing WikiAssistant components")
        self._setup_mcp_client()
        self._setup_llm()
        self._setup_chains()
        logger.info("WikiAssistant initialized successfully")
        self._chat_history = []

    async def answer(self, question: str) -> str:
        """
        Answer a user question using the wiki knowledge base.

        Args:
            question (str): The user's question

        Returns:
            str: The assistant's answer
        """
        logger.info(
            "Answer called with question length=%d", len(question) if question else 0
        )
        try:
            result = await self._qa_chain_with_context(
                {"question": question, "chat_history": self._chat_history}
            )
            answer = result["answer"]
            self._chat_history.append((question, answer))
            logger.info(
                "Answer produced successfully; history_len=%d", len(self._chat_history)
            )
            return answer
        except Exception as e:
            error_response = (
                f"I encountered an error while searching for information: {str(e)}"
            )
            logger.exception("Error in answer method")
            return error_response

    def _load_environment(self) -> None:
        """Load environment variables and validate required settings."""
        load_dotenv()

        if not self._mcp_server_url:
            raise ValueError("MCP server URL must be provided to the constructor.")

    def _setup_mcp_client(self) -> None:
        """Set up the MCP client."""
        self._mcp_client = McpSearchClient(self._mcp_server_url)
        logger.info(f"🔗 Connected to MCP server at: {self._mcp_server_url}")

    def _setup_llm(self) -> None:
        """Set up LiteLLM configuration from environment."""
        self._llm_model = os.environ.get("LLM_MODEL")
        self._llm_api_base = os.environ.get("LLM_API_BASE")
        self._llm_api_key = os.environ.get("LLM_API_KEY")

        # Normalize model to include provider prefix if missing
        def normalize_model(model: str | None, api_base: str | None) -> str | None:
            if not model:
                return model
            if "/" in model and model.split("/", 1)[0] in {"hosted_vllm"}:
                return model
            provider = "hosted_vllm"
            return f"{provider}/{model}"

        self._llm_model = normalize_model(self._llm_model, self._llm_api_base)
        logger.info(
            "LLM configuration loaded; model=%s api_base=%s",
            self._llm_model,
            self._llm_api_base,
        )

    def _is_token_error(self, error: Exception) -> bool:
        """Check if the error is related to token expiration or authentication."""
        error_str = str(error).lower()
        token_error_indicators = [
            "unauthorized",
            "authentication",
            "token",
            "expired",
            "invalid",
            "401",
            "403",
        ]
        return any(indicator in error_str for indicator in token_error_indicators)

    def _retry_with_token_refresh(self, operation, *args, **kwargs):
        """Retry an operation with token refresh if authentication fails."""
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            if self._is_token_error(e):
                logger.warning("🔄 Token appears to be expired, refreshing...")
                try:
                    self._refresh_llm_token()
                    # Recreate chains with new token
                    self._setup_chains()
                    logger.info("🔄 Retrying operation with fresh token...")
                    return operation(*args, **kwargs)
                except Exception as refresh_error:
                    logger.error(f"❌ Failed to refresh token: {refresh_error}")
                    raise e  # Re-raise original error
            else:
                raise e

    def _setup_chains(self) -> None:
        """Set up all processing chains including keyword extraction and QA."""
        logger.info("Setting up retrieval and QA chains")

        def keyword_fn(question: str) -> str:
            prompt = KEYWORD_EXTRACTION_TEMPLATE.format(question=question)
            resp = completion(
                model=self._llm_model,
                messages=[
                    {"role": "system", "content": "Extract keywords for search"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                api_base=self._llm_api_base,
                api_key=self._llm_api_key,
            )
            return resp.choices[0].message["content"] if resp and resp.choices else ""

        self._enhanced_retriever = McpKeywordEnhancedRetriever(
            mcp_client=self._mcp_client, keyword_fn=keyword_fn
        )

        # Create QA chain with context
        self._qa_chain_with_context = self._create_qa_chain_with_context()
        logger.info("Chains set up successfully")

    def _create_qa_chain_with_context(self):
        """Create a QA chain that includes document context and system prompt."""

        async def qa_with_context(inputs):
            question = inputs["question"]
            chat_history = inputs.get("chat_history", [])
            logger.info("Running QA with context; history_len=%d", len(chat_history))

            # Retrieve documents via MCP using keyword extraction
            documents: list[RetrievedDocument] = await self._enhanced_retriever.invoke(
                question
            )
            logger.info("Retrieved %d documents for QA", len(documents))

            if documents:
                doc_text = "\n\n".join(
                    [
                        f"Document {i+1}:\n{doc.page_content}"
                        for i, doc in enumerate(documents)
                    ]
                )
            else:
                doc_text = "No relevant documents found."

            def llm_call():
                prompt = QA_TEMPLATE.format(documents=doc_text, question=question)
                return completion(
                    model=self._llm_model,
                    messages=[
                        {"role": "system", "content": "Answer strictly from documents"},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    api_base=self._llm_api_base,
                    api_key=self._llm_api_key,
                )

            response = self._retry_with_token_refresh(llm_call)
            content = (
                response.choices[0].message["content"]
                if response and response.choices
                else ""
            )
            logger.info(
                "QA LLM call completed; answer_len=%d", len(content) if content else 0
            )
            return {"answer": content}

        return qa_with_context

    @property
    def chat_history(self) -> list:
        """Get the current chat history."""
        return self._chat_history.copy()

    async def close(self):
        """Close the MCP client connection."""
        if hasattr(self, "_mcp_client"):
            await self._mcp_client.close()
            logger.info("🔌 MCP client connection closed")

    def __del__(self):
        """Cleanup when the object is destroyed."""
        try:
            import asyncio

            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.close())
            else:
                loop.run_until_complete(self.close())
        except:
            pass  # Ignore cleanup errors
