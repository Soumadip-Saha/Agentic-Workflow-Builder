// src/store/workflow-store.ts
import { create } from 'zustand';
import {
  Connection,
  Edge,
  EdgeChange,
  Node,
  NodeChange,
  addEdge,
  OnNodesChange,
  OnEdgesChange,
  applyNodeChanges,
  applyEdgeChanges,
  getConnectedEdges,
} from 'reactflow';
import { v4 as uuidv4 } from 'uuid';

export type NodeData = {
  name: string;
  type: 'START' | 'END' | 'LLMNode' | 'ToolNode' | 'A2ANode';
  params?: { [key: string]: any }; 
};

type RFState = {
  nodes: Node<NodeData>[];
  edges: Edge[];
  selectedNodeId: string | null;
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  onConnect: (connection: Connection) => void;
  addNode: (nodeType: NodeData['type'], position: { x: number; y: number }) => void;
  isValidConnection: (connection: Connection) => boolean;
  deleteElements: (nodesToRemove: Node[], edgesToRemove: Edge[]) => void;
  setSelectedNodeId: (nodeId: string | null) => void;
  updateNodeParams: (nodeId: string, params: Record<string, any>) => void;
  isInteractMode: boolean;
  chatMessages: any[];
  setInteractMode: (isActive: boolean) => void;
  addChatMessage: (message: any) => void;
  streamMessage: (chunk: any) => void;
  clearChatMessages: () => void;
};

const initialNodes: Node<NodeData>[] = [
  {
    id: '1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed',
    type: 'custom', 
    position: { x: 100, y: 300 },
    data: { name: 'User Query Input', type: 'START' },
    deletable: false,
  },
  {
    id: 'c2f5f8a0-c2b1-4b7b-8b4a-4b0b1b1b1b1b',
    type: 'custom',
    position: { x: 900, y: 300 },
    data: { name: 'Final Output', type: 'END' },
    deletable: false,
  },
];

export const useWorkflowStore = create<RFState>((set, get) => ({
  nodes: initialNodes,
  edges: [],
  selectedNodeId: null,
  isInteractMode: false,
  chatMessages: [],

  onNodesChange: (changes: NodeChange[]) => {
    set({ nodes: applyNodeChanges(changes, get().nodes) });
  },
  onEdgesChange: (changes: EdgeChange[]) => {
    set({ edges: applyEdgeChanges(changes, get().edges) });
  },
  onConnect: (connection: Connection) => {
    const sourceNode = get().nodes.find(node => node.id === connection.source);
    const newEdge: Edge = {
      id: uuidv4(),
      source: connection.source!,
      target: connection.target!,
      sourceHandle: connection.sourceHandle,
      targetHandle: connection.targetHandle,
      type: sourceNode?.data.type === 'ToolNode' ? 'dashed' : 'default',
      animated: sourceNode?.data.type !== 'ToolNode',
    };
    set({ edges: addEdge(newEdge, get().edges) });
  },
  addNode: (nodeType: NodeData['type'], position: { x: number; y: number }) => {
    const newNode: Node<NodeData> = {
      id: uuidv4(),
      type: 'custom',
      position,
      data: { name: `${nodeType}`, type: nodeType, params: {} },
    };
    set({ nodes: [...get().nodes, newNode] });
  },
  isValidConnection: (connection: Connection) => {
    const { source, target, sourceHandle, targetHandle } = connection;
    const { nodes, edges } = get();
    const sourceNode = nodes.find(node => node.id === source);
    const targetNode = nodes.find(node => node.id === target);

    if (!sourceNode || !targetNode || source === target) return false;
    if (targetNode.data.type === 'START' || sourceNode.data.type === 'END') return false;
    if (targetNode.data.type === 'ToolNode') return false;

    if (sourceNode.data.type === 'ToolNode') {
      if (targetNode.data.type !== 'LLMNode' || targetHandle !== 'target-tool') return false;
    } else {
      if (targetHandle === 'target-tool') return false;
    }

    if (targetHandle === 'target-tool' && edges.some(edge => edge.target === target && edge.targetHandle === 'target-tool')) {
      return false;
    }
    
    if (targetNode.data.type === 'LLMNode' && targetHandle === 'target-direct' && edges.some(edge => edge.target === target && edge.targetHandle === 'target-direct')) {
      return false;
    }
    
    return true;
  },
  deleteElements: (nodesToRemove: Node[], edgesToRemove: Edge[]) => {
    set(state => {
      const edgesToDelete = getConnectedEdges(nodesToRemove, state.edges);
      const allEdgesToRemove = new Set([...edgesToRemove, ...edgesToDelete].map(e => e.id));
      return {
        nodes: state.nodes.filter(n => !nodesToRemove.some(ntr => ntr.id === n.id)),
        edges: state.edges.filter(e => !allEdgesToRemove.has(e.id)),
      };
    });
  },
  setSelectedNodeId: (nodeId: string | null) => {
    set({ selectedNodeId: nodeId });
  },
  updateNodeParams: (nodeId: string, newParams: Record<string, any>) => {
    set({
      nodes: get().nodes.map((node) => {
        if (node.id === nodeId) {
          const newData = { ...node.data, name: newParams.name || node.data.name, params: { ...node.data.params, ...newParams } };
          delete newData.params.name;
          return { ...node, data: newData };
        }
        return node;
      }),
    });
  },
  setInteractMode: (isActive: boolean) => {
    if (isActive) {
      get().setSelectedNodeId(null);
    }
    set({ isInteractMode: isActive });
  },
  addChatMessage: (message: any) => {
    set(state => ({ chatMessages: [...state.chatMessages, message] }));
  },
  streamMessage: (chunk: any) => {
    set(state => {
      const { chatMessages } = state;
      if (chatMessages.length === 0) {
        return { chatMessages: [chunk] };
      }
      
      const lastMessage = chatMessages[chatMessages.length - 1];
      
      // THIS IS THE CRITICAL FIX: It now checks the node_id to ensure
      // that tokens from a new agent create a new message bubble.
      const isSameStream = 
        lastMessage.node?.node_id === chunk.node?.node_id &&
        lastMessage.type === chunk.type &&
        lastMessage.stream_type === chunk.stream_type;

      if (isSameStream) {
        const updatedMessage = { ...lastMessage, content: lastMessage.content + chunk.content };
        return { chatMessages: [...chatMessages.slice(0, -1), updatedMessage] };
      } else {
        return { chatMessages: [...chatMessages, chunk] };
      }
    });
  },
  clearChatMessages: () => {
    set({ chatMessages: [] });
  },
}));