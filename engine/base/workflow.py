from pydantic import BaseModel, Field
from typing import Annotated, List
from uuid import UUID, uuid4

from .connections import AnyConnection
from .nodes import AnyNode

class WorkFlow(BaseModel):
    """The root model for the entire workflow blueprint."""
    workflow_id: UUID = Field(default_factory=uuid4)
    name: str
    nodes: List[Annotated[AnyNode, Field(discriminator="type")]]
    connections: List[Annotated[AnyConnection, Field(discriminator="type")]]

