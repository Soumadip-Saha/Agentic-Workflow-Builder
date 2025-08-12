// src/components/panels/Toolbar.tsx
import React, { DragEvent } from 'react';
import { Button } from '@/components/ui/button';
import { useWorkflowStore, NodeData } from '@/store/workflow-store';

const onDragStart = (event: DragEvent, nodeType: NodeData['type']) => {
  event.dataTransfer.setData('application/reactflow', nodeType);
  event.dataTransfer.effectAllowed = 'move';
};

export function Toolbar() {
  const { isInteractMode, setInteractMode, clearChatMessages } = useWorkflowStore();

  const handleRunClick = () => {
    // This function now toggles the interaction mode
    if (isInteractMode) {
      setInteractMode(false);
      clearChatMessages(); // Clear chat when exiting
    } else {
      clearChatMessages(); // Clear chat before starting a new session
      setInteractMode(true);
    }
  };

  return (
    <aside className="w-64 bg-gray-50 p-4 border-r border-gray-200 flex flex-col gap-4 z-10">
      <h2 className="text-lg font-bold">Nodes</h2>
      {/* Hide node palette when in interaction mode */}
      {!isInteractMode && (
        <>
          <div
            className="p-3 border-2 border-blue-400 rounded-md cursor-grab text-center bg-blue-200"
            onDragStart={(event) => onDragStart(event, 'LLMNode')}
            draggable
          >
            🤖 LLM Agent
          </div>
          <div
            className="p-3 border-2 border-yellow-400 rounded-md cursor-grab text-center bg-yellow-200"
            onDragStart={(event) => onDragStart(event, 'ToolNode')}
            draggable
          >
            🛠️ MCP Tool
          </div>
          <div
            className="p-3 border-2 border-purple-400 rounded-md cursor-grab text-center bg-purple-200"
            onDragStart={(event) => onDragStart(event, 'A2ANode')}
            draggable
          >
            🌐 A2A Agent
          </div>
        </>
      )}

      {isInteractMode && (
        <p className="text-sm text-gray-600 p-2 bg-yellow-100 rounded-md">
          Now in Chat Mode. Close this to edit the workflow.
        </p>
      )}

      <div className="mt-auto">
        {/* The button now toggles between Run and Edit modes */}
        <Button 
          className="w-full" 
          onClick={handleRunClick}
          variant={isInteractMode ? "destructive" : "default"}
        >
          {isInteractMode ? "Stop & Edit Workflow" : "Run Workflow"}
        </Button>
      </div>
    </aside>
  );
}