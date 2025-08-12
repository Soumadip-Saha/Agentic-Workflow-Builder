// src/components/panels/SettingsPanel.tsx
"use client";

import { useWorkflowStore } from "@/store/workflow-store";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { LLMNodeForm } from "./forms/LLMNodeForm";
import { ToolNodeForm } from "./forms/ToolNodeForm";
import { A2ANodeForm } from "./forms/A2ANodeForm";

export function SettingsPanel() {
  const selectedNodeId = useWorkflowStore((state) => state.selectedNodeId);
  const node = useWorkflowStore((state) => 
    state.nodes.find((n) => n.id === selectedNodeId)
  );
  const setSelectedNodeId = useWorkflowStore((state) => state.setSelectedNodeId);

  const isPanelOpen = !!node;

  const renderForm = () => {
    if (!node) return null;

    switch (node.data.type) {
      case 'LLMNode':
        return <LLMNodeForm key={node.id} node={node} />;
      case 'ToolNode':
        return <ToolNodeForm key={node.id} node={node} />;
      case 'A2ANode':
        return <A2ANodeForm key={node.id} node={node} />;
      case 'START':
      case 'END':
        return <p className="text-sm text-gray-500">This node is not configurable.</p>;
      default:
        return <p className="text-sm text-gray-500">This node type is not recognized.</p>;
    }
  };

  return (
    <Sheet open={isPanelOpen} onOpenChange={() => setSelectedNodeId(null)}>
      <SheetContent className="w-[400px] sm:w-[540px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Edit Node: {node?.data.name || 'Settings'}</SheetTitle>
        </SheetHeader>
        <div className="py-6">
          {renderForm()}
        </div>
      </SheetContent>
    </Sheet>
  );
}