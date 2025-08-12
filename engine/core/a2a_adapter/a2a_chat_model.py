import asyncio
import time
from typing import Any, List, Optional, Union
from uuid import uuid4

import httpx

# LangChain imports
from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

# A2A and our custom message imports
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    GetTaskRequest,
    JSONRPCErrorResponse,
    Message as A2ATypesMessage,
    MessageSendParams,
    SendMessageRequest,
    Task,
    TaskQueryParams,
    TextPart,
    Role,
    Part,
)
from .a2a_message import A2AMessage


class A2AChatModel(BaseChatModel):
    """
    A self-contained, LangChain-compatible Chat Model that uses an A2A
    (Agent-to-Agent) compliant agent as its backend.

    This class encapsulates all communication logic. It must be initialized
    via .initialize() or .ainitialize() before being used in a factory.
    """

    api_base_url: str
    max_retries: int = 2
    polling_interval_seconds: int = 2
    auth_token: Optional[str] = None

    # Public property to hold the agent card after initialization
    agent_card: Optional[AgentCard] = None

    # --- Internal clients and state ---
    _sync_client: Optional[httpx.Client] = None
    _async_client: Optional[httpx.AsyncClient] = None
    _sync_a2a_client: Optional[A2AClient] = None
    _async_a2a_client: Optional[A2AClient] = None

    class Config:
        arbitrary_types_allowed = True

    # --- Core LangChain properties ---
    @property
    def _llm_type(self) -> str:
        """A unique name for this type of chat model."""
        return "a2a_chat_model"

    @property
    def _identifying_params(self) -> dict[str, Any]:
        """Return a dictionary of identifying parameters for logging."""
        return {
            "api_base_url": self.api_base_url,
            "max_retries": self.max_retries,
        }

    # --- NEW: Explicit Initialization Methods ---

    async def ainitialize(self) -> None:
        """
        Performs the one-time asynchronous initialization of the client.
        Fetches the AgentCard and prepares the async client. This must be
        called before passing the model to a supervisor factory.
        """
        if self.agent_card is not None:
            return  # Already initialized

        print(f"Initializing A2A client for {self.api_base_url}...")
        transport = httpx.AsyncHTTPTransport(retries=self.max_retries)
        self._async_client = httpx.AsyncClient(transport=transport, timeout=30.0)
        
        resolver = A2ACardResolver(
            httpx_client=self._async_client, base_url=self.api_base_url
        )
        self.agent_card = await resolver.get_agent_card()
        
        self._async_a2a_client = A2AClient(
            httpx_client=self._async_client, agent_card=self.agent_card
        )
        print("Async A2A client initialized successfully.")

    def initialize(self) -> None:
        """
        Performs the one-time synchronous initialization of the client.
        This is a convenience wrapper around `ainitialize`.
        """
        if self.agent_card is not None:
            return  # Already initialized
        
        try:
            asyncio.run(self.ainitialize())
        except RuntimeError as e:
            # This can happen if an event loop is already running.
            # In such complex scenarios, the user should manage the loop
            # and call ainitialize() directly.
            print(f"Warning: Could not run synchronous initialize: {e}. "
                  "If in an async context, please use 'await model.ainitialize()' instead.")
            raise

    # --- REFACTORED: Internal Client Getters ---

    def _get_sync_a2a_client(self) -> A2AClient:
        """Returns the sync client, ensuring it's initialized."""
        if self._sync_a2a_client is None:
            if self.agent_card is None:
                # If no initialization has happened, do it now.
                self.initialize()
            
            # Now we are guaranteed to have an agent_card
            transport = httpx.HTTPTransport(retries=self.max_retries)
            self._sync_client = httpx.Client(transport=transport, timeout=30.0)
            self._sync_a2a_client = A2AClient(
                httpx_client=self._sync_client, agent_card=self.agent_card
            )
        return self._sync_a2a_client

    async def _get_async_a2a_client(self) -> A2AClient:
        """Returns the async client, ensuring it's initialized."""
        if self._async_a2a_client is None:
            # If the user forgot to call ainitialize(), do it for them.
            await self.ainitialize()
        return self._async_a2a_client

    # --- Polling Methods (Unchanged) ---

    def _poll_sync_task_until_terminal(self, task_id: str) -> Union[Task, str]:
        """Synchronously polls a task's status until it reaches a terminal state."""
        client = self._get_sync_a2a_client()
        break_states = {"completed", "cancelled", "rejected", "failed", "input-required", "auth-required"}
        while True:
            response = client.get_task(
                request=GetTaskRequest(id=uuid4().hex, params=TaskQueryParams(id=task_id))
            )
            if isinstance(response.root, JSONRPCErrorResponse):
                return f"Error polling task: {response.root.error.message}"
            task = response.root.result
            if task.status.state in break_states:
                return task
            time.sleep(self.polling_interval_seconds)

    async def _poll_async_task_until_terminal(self, task_id: str) -> Union[Task, str]:
        """Asynchronously polls a task's status until it reaches a terminal state."""
        client = await self._get_async_a2a_client()
        break_states = {"completed", "cancelled", "rejected", "failed", "input-required", "auth-required"}
        while True:
            response = await client.get_task(
                request=GetTaskRequest(id=uuid4().hex, params=TaskQueryParams(id=task_id))
            )
            if isinstance(response.root, JSONRPCErrorResponse):
                return f"Error polling task: {response.root.error.message}"
            task = response.root.result
            if task.status.state in break_states:
                return task
            await asyncio.sleep(self.polling_interval_seconds)

    # --- Core Generation Logic (Unchanged) ---

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """The core synchronous logic for interacting with the A2A agent."""
        client = self._get_sync_a2a_client()

        prompt = str(messages[-1].content)
        # Prioritize explicit state from kwargs for multi-agent scenarios
        context_id = kwargs.get("a2a_context_id")
        reference_task_ids = kwargs.get("a2a_reference_task_ids")

        # Fallback to parsing history
        if context_id is None and len(messages) > 1 and isinstance(messages[-2], A2AMessage):
            prev_msg = messages[-2]
            context_id = prev_msg.context_id
            if prev_msg.task_id:
                reference_task_ids = [prev_msg.task_id]

        message_to_send = A2ATypesMessage(
            role=Role.user,
            message_id=uuid4().hex,
            parts=[Part(root=TextPart(text=prompt))],
            context_id=context_id,
            reference_task_ids=reference_task_ids,
        )
        request = SendMessageRequest(id=uuid4().hex, params=MessageSendParams(message=message_to_send))
        response = client.send_message(request=request)

        if isinstance(response.root, JSONRPCErrorResponse):
            raise RuntimeError(f"A2A agent returned an error: {response.root.error.message}")
        
        result = response.root.result
        final_result = self._poll_sync_task_until_terminal(result.id) if isinstance(result, Task) else result
            
        if isinstance(final_result, str):
            raise RuntimeError(final_result)
        
        a2a_message = A2AMessage.from_a2a_response(final_result)
        return ChatResult(generations=[ChatGeneration(message=a2a_message)])

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """The core asynchronous logic for interacting with the A2A agent."""
        client = await self._get_async_a2a_client()

        prompt = str(messages[-1].content)
        # Prioritize explicit state from kwargs
        context_id = kwargs.get("a2a_context_id")
        reference_task_ids = kwargs.get("a2a_reference_task_ids")

        # Fallback to parsing history
        if context_id is None and len(messages) > 1 and isinstance(messages[-2], A2AMessage):
            prev_msg = messages[-2]
            context_id = prev_msg.context_id
            if prev_msg.task_id:
                reference_task_ids = [prev_msg.task_id]

        message_to_send = A2ATypesMessage(
            role=Role.user,
            message_id=uuid4().hex,
            parts=[Part(root=TextPart(text=prompt))],
            context_id=context_id,
            reference_task_ids=reference_task_ids,
        )
        request = SendMessageRequest(id=uuid4().hex, params=MessageSendParams(message=message_to_send))
        response = await client.send_message(request=request)

        # Print the response for debugging
        # print(f"Received response: {response}", flush=True)

        if isinstance(response.root, JSONRPCErrorResponse):
            raise RuntimeError(f"A2A agent returned an error: {response.root.error.message}")
        
        result = response.root.result
        final_result = await self._poll_async_task_until_terminal(result.id) if isinstance(result, Task) else result
            
        if isinstance(final_result, str):
            raise RuntimeError(final_result)
        
        a2a_message = A2AMessage.from_a2a_response(final_result)
        return ChatResult(generations=[ChatGeneration(message=a2a_message)])

    # --- Resource Cleanup Methods (Unchanged) ---
    def close(self) -> None:
        """Clean up the synchronous client resources."""
        if self._sync_client:
            self._sync_client.close()
            print("Sync A2A client closed.")

    async def aclose(self) -> None:
        """Clean up the asynchronous client resources."""
        if self._async_client:
            await self._async_client.aclose()
            print("Async A2A client closed.")