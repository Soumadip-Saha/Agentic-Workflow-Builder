import json
from uuid import uuid4

# Import necessary types and classes from your engine and libraries
from .base.workflow import WorkFlow
from .core.graph_builder import WorkflowBuilder
from .utils.agent_utils import convert_message_content_to_string
from .schemas.schema import Metadata, ChatStreamingResponse

from langchain_core.messages import HumanMessage, AIMessageChunk, ToolMessage, ToolCall
import logging
logger = logging.getLogger(__name__)
# from .core.a2a_adapter.a2a_message import A2AMessage # If needed

async def run_and_stream(workflow_blueprint: WorkFlow, query: str):
    """
    This is the core business logic generator. It:
    1. Receives a validated workflow blueprint and a query.
    2. Builds the graph.
    3. Invokes the graph.
    4. Yields formatted SSE event strings.
    """
    try:
        builder = WorkflowBuilder(workflow_blueprint)
        runnable_graph = await builder.build()
        print(f"✅ Graph built for request. Invoking with query: '{query}'")

        initial_state = {"messages": [HumanMessage(content=query)]}
        metadata = Metadata(
            worflow_id=workflow_blueprint.workflow_id,
            chat_id=uuid4(),
            run_id=uuid4(),
            user_id="vercel_user"
        )
        
        current_tool_calls = {}

        async for stream_event in runnable_graph.astream(initial_state, stream_mode=["updates", "messages", "custom"], subgraphs=True):
            namespace, stream_mode, event = stream_event[0], stream_event[1], stream_event[2]
            if not namespace:
                continue
            
            streaming_node_id = namespace[0].split(":")[0]

            if stream_mode == "messages":
                msg, emetadata = event
                if "skip_stream" in emetadata.get("tags", []):
                    continue

                response_model = None
                
                # --- YOUR FULL STREAMING LOGIC ---
                if isinstance(msg, AIMessageChunk):
                    content = convert_message_content_to_string(msg.content)
                    if msg.tool_call_chunks:
                        for chunk in msg.tool_call_chunks:
                            if chunk['index'] not in current_tool_calls:
                                current_tool_calls[chunk['index']] = {"name": chunk['name'], "args": "", "id": chunk['id']}
                            if chunk['args']:
                                current_tool_calls[chunk['index']]['args'] += chunk['args']
                    
                    if content:
                        response_model = ChatStreamingResponse(
                            node=builder.nodes_by_id[streaming_node_id],
                            content=content,
                            type="ai",
                            stream_type="token",
                            metadata=metadata
                        )
                    
                    if msg.response_metadata.get('finish_reason') == 'tool_calls' and current_tool_calls:
                        final_tool_calls = [ToolCall(name=tc['name'], args=json.loads(tc['args']), id=tc['id']) for tc in sorted(current_tool_calls.values(), key=lambda x: x['id'])]
                        response_model = ChatStreamingResponse(
                            node=builder.nodes_by_id[streaming_node_id],
                            content="",
                            type="ai",
                            stream_type="message",
                            tool_calls=final_tool_calls,
                            metadata=metadata
                        )
                        current_tool_calls = {}

                elif isinstance(msg, ToolMessage):
                    response_model = ChatStreamingResponse(
                        node=builder.nodes_by_id.get(streaming_node_id, {"name": "Unknown Tool Node"}),
                        content=convert_message_content_to_string(msg.content),
                        type="tool",
                        stream_type="message",
                        tool_call_id=msg.tool_call_id,
                        metadata=metadata
                    )

                if response_model:
                    logger.info(f"data: {response_model.model_dump_json(indent=2)}\n\n")
                    yield f"data: {response_model.model_dump_json()}\n\n"
                    

        print("✅ Graph execution finished.")

    except Exception as e:
        print(f"❌ ERROR during graph execution: {e}")
        error_response = {"type": "error", "content": f"An error occurred: {str(e)}"}
        yield f"data: {json.dumps(error_response)}\n\n"