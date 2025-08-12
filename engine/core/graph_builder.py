import asyncio
import os
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient

from ..base.models import SelfHostedConfig

# from settings.app_settings import settings
from ..base.workflow import WorkFlow
from ..base.nodes import A2ANode, LLMNode, ToolNode, StartNode, EndNode
from ..base.connections import ConditionalConnection, LLMToolConnection, DirectConnection
from .a2a_adapter.a2a_chat_model import A2AChatModel
from ..validators.llm_validator import check_llm_node_connectivity
from ..validators.tool_validator import check_tool_node_connectivity, convert_toolnode_to_langchain_mcp_config
from langgraph.prebuilt.chat_agent_executor import AgentState

class WorkflowBuilder:
    """
    Compiles a WorkFlow blueprint into a runnable, high-level LangGraph StateGraph
    where each node is a self-contained agent created with a factory like `create_react_agent`.
    """

    # --- 1. PUBLIC INTERFACE ---

    def __init__(self, workflow_blueprint: WorkFlow):
        """
        The constructor takes the validated Pydantic model as its input.
        It initializes the main graph and creates convenient lookups for efficiency.
        """
        print("Initializing WorkflowBuilder...")
        self.workflow = workflow_blueprint
        self.main_graph = StateGraph(AgentState)
        
        # Pre-process nodes and connections into dictionaries for fast lookups.
        self.nodes_by_id = {str(node.node_id): node for node in self.workflow.nodes}
        
        # A specific lookup for tool connections to make agent-building easier.
        self.tool_connections_by_llm_id = self._group_tool_connections()
    
    async def _run_pre_flight_checks(self):
        validation_checks = []
        for node in self.workflow.nodes:
            if isinstance(node, LLMNode):
                task = check_llm_node_connectivity(node)
                validation_checks.append(task)
            elif isinstance(node, ToolNode):
                task = check_tool_node_connectivity([node])
                validation_checks.append(task)
        
        # start validation checks
        results = await asyncio.gather(*validation_checks, return_exceptions=True)

        # check for failures
        failed_checks = [res for res in results if isinstance(res, Exception)]
        if failed_checks:
            error_messages = "\n".join([f"  - {type(e).__name__}: {e}" for e in failed_checks])
            raise ConnectionError(
                f"Workflow build failed. One or more pre-flight checks did not pass:\n{error_messages}"
            )


    async def build(self):
        """
        This is the main public method. It orchestrates the compilation process
        and returns the final, compiled, runnable graph.
        """

        await self._run_pre_flight_checks()

        print("--- Starting Graph Build Process ---")
        
        # The build process is now a clean, two-step pipeline.
        await self._add_agent_nodes_to_graph()
        self._add_orchestration_edges_to_graph()
        
        print("\n--- Compiling Main Graph ---")

        compiled_graph = self.main_graph.compile()
        print("✅ Main graph compiled successfully!")
        return compiled_graph


    # --- 2. PRIVATE HELPER METHODS (The Build Pipeline) ---

    async def _add_agent_nodes_to_graph(self):
        """
        (BUILD STEP 1 - REVISED AND IMPROVED)
        This method is the core of the agent creation logic.
        It iterates through all blueprint nodes. For each `LLMNode`, it finds its
        dedicated tools, compiles a complete agent using `create_react_agent`,
        and adds this compiled agent as a single node to the main graph.
        """
        print("\nStep 1: Compiling and adding agent nodes...")
        for node_id_str, node in self.nodes_by_id.items():
            if isinstance(node, A2ANode):
                print(f"  - Found A2ANode '{node.name}'. Skipping as it is not an agent.")
                a2a_chat_model = A2AChatModel(api_base_url=str(node.api_base_url))
                await a2a_chat_model.ainitialize()
                compiled_agent = create_react_agent(
                    model=a2a_chat_model,
                    tools=[],
                    name=node_id_str
                )
                # 5. Add the fully compiled agent as ONE node to the main graph.
                self.main_graph.add_node(node_id_str, compiled_agent)
                print(f"    - ✅ Successfully added compiled agent '{compiled_agent.name}' to the main graph.")
            elif isinstance(node, LLMNode):
                print(f"  - Found LLMNode '{node.name}'. Beginning agent compilation...")
                
                # 1. Get the specific tools for this agent.
                agent_tool_blueprints = self.tool_connections_by_llm_id.get(node_id_str, [])
                mcp_servers_config = convert_toolnode_to_langchain_mcp_config(agent_tool_blueprints)
                mcp_servers = MultiServerMCPClient(connections=mcp_servers_config)
                agent_tools = await mcp_servers.get_tools()
                print(f"    - Agent will have {len(agent_tool_blueprints)} tools.")
                
                # 2. Get the LLM client for this agent.
                #    (This would call the get_llm_client service function)
                
                model_provider = node.model.config.model_provider
                # If the model provider is self-hosted, use "openai" instead for openai-compatible server
                
                
                if isinstance(node.model.config, SelfHostedConfig):
                    model_provider = "openai"
                    api_key = node.model.config.api_key_name
                    base_url = node.model.config.base_url
                
                    llm_client = init_chat_model(
                        model=node.model.config.model,
                        model_provider=model_provider,
                        temperature=node.parameters.temperature,
                        max_tokens=node.parameters.max_tokens,
                        api_key=api_key,
                        base_url=base_url
                    )
                else:
                    api_key = os.getenv(node.model.config.api_key_name)
                    if not api_key:
                        raise ValueError(f"API key for {model_provider} not found in environment variables.")
                    llm_client = init_chat_model(
                        model=node.model.config.model,
                        model_provider=model_provider,
                        temperature=node.parameters.temperature,
                        max_tokens=node.parameters.max_tokens,
                        api_key=api_key
                    )
                
                # 3. Define the prompt for this agent.
                #    (This could be customized or loaded from the blueprint in the future)
                prompt = node.parameters.system_prompt
                
                # 4. Use the `create_react_agent` factory to build the runnable agent.
                #    This is the key step you identified.
                print(f"    - Calling `create_react_agent` for '{node.name}'...")
                compiled_agent = create_react_agent(
                    model=llm_client,
                    tools=agent_tools,
                    prompt=prompt,
                    name=node_id_str
                )
                
                # 5. Add the fully compiled agent as ONE node to the main graph.
                self.main_graph.add_node(node_id_str, compiled_agent)
                print(f"    - ✅ Successfully added compiled agent '{compiled_agent.name}' to the main graph.")
            else:
                # We only create graph nodes for LLMNodes and A2ANode.
                # Start, End, and Tool nodes are metadata for the builder.
                continue


    def _add_orchestration_edges_to_graph(self):
        """
        (BUILD STEP 2)
        Connects the compiled agent nodes within `self.main_graph`. This method
        is responsible for setting the graph's entry point and adding the
        high-level control flow edges (`direct` and `conditional`) between agents.
        """
        print("\nStep 2: Adding orchestration edges between agents...")
        # The logic for this method remains the same as previously discussed:
        # - Find the StartNode and set the entry point.
        # - Iterate through connections. If a connection is `direct` or `conditional`
        #   and is between two LLMNodes, add an edge or conditional edge to the main_graph.
        # - It will ignore `LLMToolConnection`s.
        self._set_entry_point()

        for conn in self.workflow.connections:
            source_node_id = str(conn.source_node_id)

            # Skip connections from START (already handled) and non-agent nodes. Currently there are two types of agent nodes: LLMNode and A2ANode.
            if not isinstance(self.nodes_by_id.get(source_node_id), (LLMNode, A2ANode)):
                continue

            if isinstance(conn, DirectConnection):
                dest_node_id = str(conn.destination_node_id)
                # Check if the destination is the END node
                if isinstance(self.nodes_by_id.get(dest_node_id), EndNode):
                    self.main_graph.add_edge(source_node_id, END)
                elif dest_node_id in self.main_graph.nodes:
                    self.main_graph.add_edge(source_node_id, dest_node_id)
            
            elif isinstance(conn, ConditionalConnection):
                # TODO: Implement later
                raise NotImplementedError("Yet to be implemented")
            else:
                # skip the LLMToolConnection because it is handled in the agent building
                continue

    def _set_entry_point(self):
        """
        Finds the unique START node and its single outgoing connection to set
        the graph's entry point. Enforces the rule that there can be only one.
        """
        print("  - Identifying graph entry point...")
        
        # 1. Find the START node itself.
        start_nodes = [n for n in self.workflow.nodes if isinstance(n, StartNode)]
        if len(start_nodes) == 0:
            raise ValueError("Workflow Build Error: The blueprint must have exactly one START node, but none was found.")
        if len(start_nodes) > 1:
            raise ValueError(f"Workflow Build Error: The blueprint must have exactly one START node, but {len(start_nodes)} were found.")
        start_node = start_nodes[0]

        # 2. Find all direct connections leaving the START node.
        outgoing_connections = [
            conn for conn in self.workflow.connections 
            if str(conn.source_node_id) == str(start_node.node_id) and isinstance(conn, DirectConnection)
        ]
        
        # 3. Enforce the "single connection" rule.
        if len(outgoing_connections) == 0:
            raise ValueError(f"Workflow Build Error: The START node '{start_node.name}' is not connected to any other node.")
        if len(outgoing_connections) > 1:
            dest_names = [self.nodes_by_id.get(str(c.destination_node_id)).name for c in outgoing_connections]
            raise ValueError(
                f"Workflow Build Error: The START node '{start_node.name}' has multiple outgoing direct connections "
                f"(to: {', '.join(dest_names)}). It must have exactly one to define a clear entry point."
            )

        # 4. If all checks pass, set the entry point using the node's unique ID.
        entry_point_conn = outgoing_connections[0]
        entry_point_node_id = str(entry_point_conn.destination_node_id)
        
        # Final check to ensure the destination is a valid agent node
        if entry_point_node_id not in self.main_graph.nodes:
             raise ValueError(f"Workflow Build Error: The START node connects to node '{entry_point_node_id}', but this node was not compiled as an agent. The START node must connect to an LLMNode.")
        
        print(f"  - ✅ Set graph entry point to '{self.nodes_by_id[entry_point_node_id].name}' ({entry_point_node_id})")
        self.main_graph.set_entry_point(entry_point_node_id)

    
    # --- 3. UTILITY METHODS ---
    
    def _group_tool_connections(self) -> dict[str, list[ToolNode]]:
        """
        (Called in __init__)
        A utility to pre-process the connections list to create a highly efficient
        lookup mapping an LLMNode's ID to a list of its dependent ToolNodes.
        """
        tool_deps = {}
        for conn in self.workflow.connections:
            if isinstance(conn, LLMToolConnection):
                dest_id = str(conn.destination_node_id)
                source_node = self.nodes_by_id.get(str(conn.source_node_id))
                if dest_id not in tool_deps:
                    tool_deps[dest_id] = []
                if isinstance(source_node, ToolNode):
                    tool_deps[dest_id].append(source_node)
        return tool_deps
        
