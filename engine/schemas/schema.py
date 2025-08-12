from pydantic import BaseModel, Field
from typing import Optional, Literal
from uuid import UUID, uuid4
from ..base.nodes import AnyNode
from langchain_core.messages import ToolCall



class BaseResponse(BaseModel):
    name: str
    id: UUID = Field(default_factory=uuid4)

class AIResponse(BaseResponse):
    type: Literal["AIResponse"]
    content: str
    tool_calls: list[ToolCall]


class Metadata(BaseModel):
    """A Pydantic model for metadata associated with a chat request."""
    worflow_id: UUID = Field(description="The ID of the workflow to which the request belongs.")
    chat_id: UUID = Field(description="The ID the chat associated with the user.", default_factory=uuid4)
    run_id: UUID = Field(description="The ID of the run associated with the request.", default_factory=uuid4)
    user_id: str = Field(description="The ID of the user making the request.", default="default_user") 

class ChatRequest(BaseModel):
    """A Pydantic model for chat requests."""
    query: str = Field(..., description="The user's query or message.")
    metadata: Metadata
       
class ChatStreamingResponse(BaseModel):
    """A Pydantic model for chat responses."""
    node: AnyNode
    content: str = Field(..., description="The content of the response.")
    type: Literal["human", "ai", "tool", "custom"] = Field(description="Role of the message.", examples=["human", "ai", "tool", "custom"])
    stream_type: Literal["token", "message"] = Field(..., description="The type of response, either 'token' or 'message'.")
    tool_calls: list[ToolCall] = Field(
        description="Tool calls in the message.", default=[]
    )
    tool_call_id: Optional[str] = Field(
        description="Tool call that this message is responding to.",
        default=None,
        examples=["123456789"],
    )
    metadata: Metadata