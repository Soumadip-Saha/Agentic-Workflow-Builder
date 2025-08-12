from typing import List, Optional, Union

# LangChain's core message class
from langchain_core.messages import AIMessage

# A2A's specific data types from your types.py
from a2a.types import Task, Message as A2ATypesMessage, Artifact, TextPart

class A2AMessage(AIMessage):
    """
    An extension of LangChain's AIMessage to natively handle the rich,
    structured data from the A2A protocol.

    This class is compatible with the LangChain ecosystem while providing
    first-class access to A2A-specific concepts like tasks, contexts,
    and artifacts.
    """

    # --- A2A-Specific Fields ---
    task_id: Optional[str] = None
    context_id: Optional[str] = None
    artifacts: List[Artifact] = []

    # Store the original, complete A2A response object for full data fidelity.
    # This is useful if you need to access any data not exposed directly.
    a2a_source: Optional[Union[Task, A2ATypesMessage]] = None
    
    # Let LangChain know this is our new, unique type
    type: str = "a2a"

    @staticmethod
    def _extract_content_from_parts(parts: List) -> Union[str, list]:
        """A helper to convert A2A Parts into LangChain content."""
        lc_content = []
        for part in parts:
            if isinstance(part.root, TextPart):
                # For simple text parts, just append the string
                lc_content.append(part.root.text)
            else:
                # For more complex parts (FilePart, DataPart), append
                # their dictionary representation. LangChain handles this.
                lc_content.append(part.root.model_dump())
        
        # If the content is just a single string, return that.
        # Otherwise, return the list of parts.
        if len(lc_content) == 1 and isinstance(lc_content[0], str):
            return lc_content[0]
        return lc_content

    @classmethod
    def from_a2a_response(
        cls, response: Union[Task, A2ATypesMessage]
    ) -> "A2AMessage":
        """
        A factory method to create an A2AMessage from a raw A2A Task or Message.
        
        This is the primary bridge between the A2A client's output and the
        LangChain ecosystem.
        """
        if isinstance(response, Task):
            # If the response is a Task, the primary content is usually in the artifacts.
            # We will take the content from the parts of the *first* artifact for simplicity.
            # A more complex strategy could combine content from all artifacts.
            content_parts = response.artifacts[0].parts if response.artifacts else []
            final_content = cls._extract_content_from_parts(content_parts)

            return cls(
                content=final_content,
                task_id=response.id,
                context_id=response.context_id,
                artifacts=response.artifacts or [],
                a2a_source=response,
                # Pass the original task's status into LangChain's metadata field
                response_metadata={"status": response.status.model_dump()},
            )
        
        elif isinstance(response, A2ATypesMessage):
            # If the response is a direct Message, its content is in its own parts.
            final_content = cls._extract_content_from_parts(response.parts)

            return cls(
                content=final_content,
                task_id=response.task_id,
                context_id=response.context_id,
                artifacts=[],  # Direct messages don't have artifacts
                a2a_source=response,
            )
        
        else:
            raise TypeError(
                f"Unsupported A2A response type for message conversion: {type(response)}"
            )