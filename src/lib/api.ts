// src/lib/api.ts
import { useWorkflowStore } from "@/store/workflow-store";
import { v4 as uuidv4 } from 'uuid';

const generateWorkflowPayload = () => {
  const { nodes, edges } = useWorkflowStore.getState();
  
  const workflowNodes = nodes.map(node => {
    const { type, name } = node.data;

    // This switch statement builds the exact JSON structure your Pydantic
    // models and their @model_validator functions are expecting.
    switch (type) {
      case 'LLMNode':
        const params = node.data.params || {};
        return {
          type: "LLMNode",
          node_id: node.id,
          name: name,
          // The param_dict wrapper is correctly included.
          param_dict: {
            model: {
              config: {
                model_provider: params.modelProvider,
                model: params.model,
                // The field name is 'api_key_name', as your Pydantic model requires.
                api_key_name: params.apiKeyName,
              }
            },
            parameters: {
              temperature: params.temperature,
              system_prompt: params.systemPrompt,
            }
          }
        };
      
      case 'ToolNode':
        return {
          type: "ToolNode",
          node_id: node.id,
          name: name,
          param_dict: {
            tool_endpoint: node.data.params?.toolEndpoint
          }
        };

      case 'A2ANode':
        return {
          type: "A2ANode",
          node_id: node.id,
          name: name,
          param_dict: {
            api_base_url: node.data.params?.apiBaseUrl
          }
        };

      case 'START':
      case 'END':
      default:
        // START and END nodes have no param_dict.
        return {
          type: type,
          node_id: node.id,
          name: name
        };
    }
  });

  const workflowConnections = edges.map(edge => {
    const sourceNode = nodes.find(n => n.id === edge.source)!;
    return {
      type: sourceNode.data.type === 'ToolNode' ? 'tool-connection' : 'direct',
      connection_id: edge.id,
      source_node_id: edge.source,
      destination_node_id: edge.target,
    };
  });

  return {
    workflow_id: uuidv4(),
    name: "My Awesome Workflow",
    nodes: workflowNodes,
    connections: workflowConnections,
  };
};


// The API calling function with the final correct endpoint URL.
export const callInvokeAPI = async (
  query: string,
  streamMessage: (chunk: any) => void,
  addChatMessage: (message: any) => void
) => {
  const workflowPayload = generateWorkflowPayload();

  try {
    // THIS IS THE FINAL, CORRECT URL for our streaming proxy.
    const response = await fetch('/api/invoke', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        workflow: workflowPayload,
        query: query,
      }),
    });

    // Error handling for Pydantic validation failures
    if (response.status === 422) {
        const errorBody = await response.json();
        console.error("PYDANTIC VALIDATION ERROR:", JSON.stringify(errorBody, null, 2));
        addChatMessage({ type: 'error', content: 'The workflow configuration is invalid. Check the browser console for details.' });
        return;
    }
    // Error handling for other server errors
    if (!response.ok || !response.body) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    // Logic for processing the stream
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n\n').filter(line => line.trim().startsWith('data: '));

      for (const line of lines) {
        const jsonStr = line.substring(6);
        try {
          const parsedJson = JSON.parse(jsonStr);
          if (parsedJson.stream_type === 'token') {
            streamMessage(parsedJson);
          } else {
            addChatMessage(parsedJson);
          }
        } catch (e) {
          console.error("Failed to parse JSON chunk:", jsonStr, e);
        }
      }
    }
  } catch (error) {
    console.error("API call failed:", error);
    const errorMessage = { type: 'error', content: 'Failed to get response from the server.' };
    addChatMessage(errorMessage);
  }
};