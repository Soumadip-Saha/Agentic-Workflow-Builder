from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class BaseNode(BaseModel):
    """The absolute base for all nodes. Contains only the universally required fields."""
    name: str
    node_id: UUID = Field(default_factory=uuid4)

class BaseConnection(BaseModel):
    """
    The absolute base class for all connections in the workflow.
    It contains fields universally required for any edge in the graph.
    
    Args:
        connection_id (UUID): A unique identifier for the connection.
        source_node_id (UUID): The ID of the source node.
        destination_node_id (UUID): The ID of the destination node.
    """
    connection_id: UUID = Field(default_factory=uuid4)
    source_node_id: UUID
    destination_node_id: UUID

