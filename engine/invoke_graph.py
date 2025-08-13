# engine/invoke_graph.py

import json
from uuid import uuid4
import logging
from .base.workflow import WorkFlow
from .core.graph_builder import WorkflowBuilder
from .utils.agent_utils import convert_message_content_to_string
from .schemas.schema import Metadata, ChatStreamingResponse

from langchain_core.messages import HumanMessage, AIMessageChunk, ToolMessage, ToolCall

# Configure basic logging to capture messages from this module
# Vercel collects stdout/stderr, so this will appear in Vercel logs
logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger(__name__)



async def run_and_stream(workflow_blueprint: WorkFlow, query: str):
    """
    This is the core business logic generator. It:
    1. Receives a validated workflow blueprint and a query.
    2. Builds the graph.
    3. Invokes the graph.
    4. Yields formatted SSE event strings.
    """
    logger.info(f"⚡️ [run_and_stream] Starting for workflow: {workflow_blueprint.workflow_id}, query: '{query}'")
    try:
        builder = WorkflowBuilder(workflow_blueprint)
        logger.info("🛠️ [run_and_stream] Attempting to build graph...")
        runnable_graph = await builder.build()
        logger.info("✅ [run_and_stream] Graph built successfully.")

        initial_state = {"messages": [HumanMessage(content=query)]}
        metadata = Metadata(
            worflow_id=workflow_blueprint.workflow_id,
            chat_id=uuid4(),
            run_id=uuid4(),
            user_id="vercel_user"
        )
        
        current_tool_calls = {}

        logger.info("🚀 [run_and_stream] Starting graph astream invocation...")
        async for stream_event in runnable_graph.astream(initial_state, stream_mode=["updates", "messages", "custom"], subgraphs=True):
            namespace, stream_mode, event = stream_event[0], stream_event[1], stream_event[2]
            
            # Using logger.debug for very verbose events to avoid cluttering info logs
            logger.debug(f"🔍 [run_and_stream] Raw Stream Event: namespace={namespace}, mode={stream_mode}, event_type={type(event)}")

            if not namespace:
                logger.debug("Skipping event with empty namespace.")
                continue
            
            streaming_node_id = namespace[0].split(":")[0]
            
            # Ensure the node object is correctly extracted for logging
            node_name = builder.nodes_by_id.get(streaming_node_id, {}).get("name", "UnknownNode")

            if stream_mode == "messages":
                msg, emetadata = event
                logger.debug(f"📦 [run_and_stream] Message Event: from {node_name}, type={type(msg)}, content={getattr(msg, 'content', 'N/A')}")

                if "skip_stream" in emetadata.get("tags", []):
                    logger.info(f"🚫 [run_and_stream] Skipping stream for message with 'skip_stream' tag from {node_name}.")
                    continue

                response_model = None
                
                # --- YOUR FULL STREAMING LOGIC ---
                if isinstance(msg, AIMessageChunk):
                    content = convert_message_content_to_string(msg.content)
                    if msg.tool_call_chunks:
                        logger.info(f"🔧 [run_and_stream] Tool call chunks received from {node_name}.")
                        for chunk in msg.tool_call_chunks:
                            if chunk['index'] not in current_tool_calls:
                                current_tool_calls[chunk['index']] = {"name": chunk['name'], "args": "", "id": chunk['id']}
                            if chunk['args']:
                                current_tool_calls[chunk['index']]['args'] += chunk['args']
                    
                    if content:
                        logger.debug(f"✍️ [run_and_stream] Streaming token content from {node_name}: '{content}'")
                        response_model = ChatStreamingResponse(
                            node=builder.nodes_by_id[streaming_node_id],
                            content=content,
                            type="ai",
                            stream_type="token",
                            metadata=metadata
                        )
                    
                    if msg.response_metadata.get('finish_reason') == 'tool_calls' and current_tool_calls:
                        logger.info(f"✅ [run_and_stream] AI finished with tool calls from {node_name}.")
                        final_tool_calls = [ToolCall(name=tc['name'], args=json.loads(tc['args']), id=tc['id']) for tc in sorted(current_tool_calls.values(), key=lambda x: x['id'])]
                        response_model = ChatStreamingResponse(
                            node=builder.nodes_by_id[streaming_node_id],
                            content="",
                            type="ai",
                            stream_type="message", # This is a full message, not a token
                            tool_calls=final_tool_calls,
                            metadata=metadata
                        )
                        current_tool_calls = {} # Reset for next potential tool call

                elif isinstance(msg, ToolMessage):
                    logger.info(f"✅ [run_and_stream] Tool execution result from {node_name}.")
                    response_model = ChatStreamingResponse(
                        node=builder.nodes_by_id.get(streaming_node_id, {"name": "Unknown Tool Node"}), # Fallback for unknown node
                        content=convert_message_content_to_string(msg.content),
                        type="tool",
                        stream_type="message", # This is a full message, not a token
                        tool_call_id=msg.tool_call_id,
                        metadata=metadata
                    )

                # Assuming A2AMessage is also part of your schema and has similar structure
                # elif isinstance(msg, A2AMessage):
                #    logger.info(f"🌐 [run_and_stream] A2A Message received from {node_name}.")
                #    content = convert_message_content_to_string(msg.content)
                #    if content:
                #        response_model = ChatStreamingResponse(
                #            node=builder.nodes_by_id[streaming_node_id],
                #            content=content,
                #            type="ai", # Or "a2a" if you want a distinct type in frontend
                #            stream_type="message",
                #            metadata=metadata
                #        )

                if response_model:
                    # Yield the JSON string for the SSE stream
                    logger.info(f"➡️ [run_and_stream] Yielding data from {node_name}: {response_model.stream_type}")
                    yield f"data: {response_model.model_dump_json()}\n\n"

        logger.info("✅ [run_and_stream] Graph execution finished.")

    except Exception as e:
        logger.exception("❌ [run_and_stream] FATAL ERROR during graph execution.") # Log full traceback
        error_response = {
            "type": "error",
            "content": f"An unexpected error occurred in the backend: {str(e)}",
            "full_traceback": True # Flag for frontend to know it's a critical error
        }
        # Yield the error response to the frontend
        yield f"data: {json.dumps(error_response)}\n\n"