from pydantic import Field
from typing import Literal, Union

from .common import BaseConnection

class DirectConnection(BaseConnection):
    """A simple, direct uni directional connection from one node to another."""
    type: Literal["direct"] = "direct"

class ConditionalConnection(BaseConnection):
    """
    A connection that is only taken if a condition is met.
    This is used for branching logic in the graph.
    """
    type: Literal["conditional"] = "conditional"
    condition: str = Field(..., description="A condition to evaluate, e.g., '{{ #input.value > 10 }}'")

class LLMToolConnection(BaseConnection):
    """A connection from tool to LLM. This connection can be used to pass data from a tool to an LLM back and forth."""
    type: Literal["tool-connection"] = "tool-connection"

AnyConnection = Union[DirectConnection, ConditionalConnection, LLMToolConnection]