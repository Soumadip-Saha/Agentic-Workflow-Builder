// src/app/page.tsx
'use client';

import React, { DragEvent, useCallback, useRef, useMemo } from 'react';
import ReactFlow, {
  Controls,
  Background,
  ReactFlowProvider,
  ReactFlowInstance,
  Node,
  MarkerType,
  BackgroundVariant,
  BaseEdge,
  EdgeProps,
  getStraightPath,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { useWorkflowStore } from '@/store/workflow-store';
import { Toolbar } from '@/components/panels/Toolbar';
import CustomNode from '@/components/nodes/CustomNode';
import { SettingsPanel } from '@/components/panels/SettingsPanel';
// CHANGE 1: Import the InteractNode component here directly.
import { InteractNode } from '@/components/nodes/InteractNode';

const nodeTypes = {
  custom: CustomNode,
};

const connectionLineStyle = { stroke: '#2563eb', strokeWidth: 2 };

export default function WorkflowBuilderPage() {
  // CHANGE 2: Get the isInteractMode flag from the store.
  const { 
    nodes, 
    edges, 
    onNodesChange, 
    onEdgesChange, 
    onConnect, 
    addNode, 
    isValidConnection,
    deleteElements,
    setSelectedNodeId,
    isInteractMode, // <-- Get the flag
  } = useWorkflowStore();
  
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = React.useState<ReactFlowInstance | null>(null);

  const onDragOver = useCallback((event: DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: DragEvent) => {
      event.preventDefault();
      const type = event.dataTransfer.getData('application/reactflow') as any;
      if (typeof type === 'undefined' || !type || !reactFlowWrapper.current || !reactFlowInstance) return;
      const position = reactFlowInstance.screenToFlowPosition({ x: event.clientX, y: event.clientY });
      addNode(type, position);
    },
    [reactFlowInstance, addNode]
  );

  const onNodesDelete = useCallback(
    (deleted: Node[]) => {
      deleteElements(deleted, []);
    },
    [deleteElements],
  );

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    // CHANGE 3: Prevent opening settings panel if in interact mode.
    if (!isInteractMode) {
      setSelectedNodeId(node.id);
    }
  }, [setSelectedNodeId, isInteractMode]);

  const onPaneClick = useCallback(() => {
    setSelectedNodeId(null);
  }, [setSelectedNodeId]);

  const defaultEdgeOptions = {
    markerEnd: { type: MarkerType.ArrowClosed, color: '#2563eb' },
    style: { stroke: '#2563eb', strokeWidth: 2 },
  };

  const edgeTypes = useMemo(() => ({
    dashed: ({ id, sourceX, sourceY, targetX, targetY, markerEnd, style }: EdgeProps) => {
      const [edgePath] = getStraightPath({ sourceX, sourceY, targetX, targetY });
      return (
        <BaseEdge 
          id={id} 
          path={edgePath} 
          markerEnd={markerEnd} 
          style={{ ...style, stroke: '#facc15', strokeWidth: 2, strokeDasharray: '5 5' }} 
        />
      );
    },
  }), []);

  return (
    // CHANGE 4: Add 'relative' positioning to the main container.
    <div className="flex h-screen w-screen flex-row bg-white relative">
      <Toolbar />
      <SettingsPanel />

      {/* CHANGE 5: Conditionally render the InteractNode as a floating panel. */}
      {isInteractMode && (
        <div className="absolute top-4 right-4 z-20">
          <InteractNode />
        </div>
      )}

      <div className="flex-grow h-full" ref={reactFlowWrapper}>
        <ReactFlowProvider>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodesDelete={onNodesDelete}
            onConnect={onConnect}
            isValidConnection={isValidConnection}
            onInit={setReactFlowInstance}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            defaultEdgeOptions={defaultEdgeOptions}
            connectionLineStyle={connectionLineStyle}
            fitView

            // CHANGE 6: Lock the canvas when in interact mode.
            nodesDraggable={!isInteractMode}
            nodesConnectable={!isInteractMode}
            elementsSelectable={!isInteractMode}
            panOnDrag={!isInteractMode}
            zoomOnScroll={!isInteractMode}
            zoomOnPinch={!isInteractMode}
            zoomOnDoubleClick={!isInteractMode}
          >
            <Controls />
            <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
          </ReactFlow>
        </ReactFlowProvider>
      </div>
    </div>
  );
}