from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StreamableHttpConnection, SSEConnection, Connection
import logging


from ..base.nodes import ToolNode

def convert_toolnode_to_langchain_mcp_config(nodes: list[ToolNode]) -> dict[str, Connection]:
    mcp_servers = {}
    for node in nodes:
        if str(node.tool_endpoint).endswith("/mcp"):
            # Remove trailing /mcp if present
            mcp_servers[node.name] = StreamableHttpConnection(
                url=str(node.tool_endpoint), transport="streamable_http"
            )
        elif str(node.tool_endpoint).endswith("/sse"):
            # Use SSEConnection for SSE endpoints
            mcp_servers[node.name] = SSEConnection(
                url=str(node.tool_endpoint), transport="sse"
            )
        else:
            # Default to StreamableHttpConnection for other endpoints
            raise ValueError(
                f"Unsupported tool endpoint format: {node.tool_endpoint}. "
                "Expected format should end with '/mcp' or '/sse'."
            )
    
    return mcp_servers

async def check_tool_node_connectivity(nodes: list[ToolNode]):
    """Checks if tool servers are reachable and has tools."""
    try:
        mcp_servers = convert_toolnode_to_langchain_mcp_config(nodes)
        client = MultiServerMCPClient(mcp_servers)
        tools = await client.get_tools()

        if not tools:
            raise ValueError("Server is reachable, but no tools were found.")
        
        logging.info(f"Successfully connected to {', '.join([node.name for node in nodes])} and found {', '.join([tool.name for tool in tools])} tools.")
    except Exception as e:
        raise ConnectionError(f"The tool endpoints are not responding or failed. Error: {e}")
    