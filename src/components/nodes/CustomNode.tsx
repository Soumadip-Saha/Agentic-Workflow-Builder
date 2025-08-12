// src/components/nodes/CustomNode.tsx
import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { NodeData } from '@/store/workflow-store';

// CHANGE 1: The import for InteractNode has been removed.

const CustomNode = ({ data, isConnectable }: NodeProps<NodeData>) => {
  const { name, type } = data;

  // CHANGE 2: The special "if (type === 'InteractNode')" block is GONE.

  // This logic is now the start of the component.
  const getNodeStyle = (nodeType: NodeData['type']) => {
    switch (nodeType) {
      case 'START':
        return { icon: '▶️', bgColor: 'bg-green-200', borderColor: 'border-green-400' };
      case 'END':
        return { icon: '⏹️', bgColor: 'bg-red-200', borderColor: 'border-red-400' };
      case 'LLMNode':
        return { icon: '🤖', bgColor: 'bg-blue-200', borderColor: 'border-blue-400' };
      case 'ToolNode':
        return { icon: '🛠️', bgColor: 'bg-yellow-200', borderColor: 'border-yellow-400' };
      case 'A2ANode':
        return { icon: '🌐', bgColor: 'bg-purple-200', borderColor: 'border-purple-400' };
      // CHANGE 3: The 'InteractNode' case is REMOVED from the switch.
      default:
        // This default is never really used but is good practice.
        return { icon: '📄', bgColor: 'bg-gray-200', borderColor: 'border-gray-400' };
    }
  };

  const { icon, bgColor, borderColor } = getNodeStyle(type);

  const showDefaultSource = type !== 'END';
  const showDefaultTarget = type !== 'START' && type !== 'ToolNode' && type !== 'LLMNode';

  return (
    <div className={`w-48 p-3 rounded-lg border-2 ${bgColor} ${borderColor} relative`}>
      {/* Default Target Handle (for A2A, END) */}
      {showDefaultTarget && (
        <Handle
          type="target"
          position={Position.Left}
          className="!bg-gray-500"
          isConnectable={isConnectable}
        />
      )}

      {/* Specialised Handles for LLMNode */}
      {type === 'LLMNode' && (
        <>
          <Handle
            type="target"
            id="target-direct"
            position={Position.Left}
            className="!bg-gray-500"
            style={{ top: '33%' }}
            isConnectable={isConnectable}
          />
          <Handle
            type="target"
            id="target-tool"
            position={Position.Left}
            className="!bg-yellow-500 !border-yellow-600"
            style={{ top: '66%' }}
            isConnectable={isConnectable}
          />
        </>
      )}

      <div className="flex items-center gap-2">
        <span className="text-xl">{icon}</span>
        <strong className="text-sm">{name}</strong>
      </div>
      
      {/* Default Source Handle */}
      {showDefaultSource && (
        <Handle
          type="source"
          position={Position.Right}
          className="!bg-gray-500"
          isConnectable={isConnectable}
        />
      )}
    </div>
  );
};

export default memo(CustomNode);