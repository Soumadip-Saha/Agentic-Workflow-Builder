// src/components/panels/forms/ToolNodeForm.tsx
"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { ToolNodeSchema } from "@/lib/schemas"
import { useWorkflowStore } from "@/store/workflow-store"
import { Node } from "reactflow"
import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"

type ToolFormValues = z.infer<typeof ToolNodeSchema>

interface ToolNodeFormProps {
  node: Node;
}

export function ToolNodeForm({ node }: ToolNodeFormProps) {
  const updateNodeParams = useWorkflowStore((state) => state.updateNodeParams)

  const form = useForm<ToolFormValues>({
    resolver: zodResolver(ToolNodeSchema),
    defaultValues: {
      name: node.data.name || "MCP Tool",
      toolEndpoint: node.data.params?.toolEndpoint || "",
    },
  })

  function onSubmit(values: ToolFormValues) {
    updateNodeParams(node.id, values)
  }

  return (
    <Form {...form}>
      {/* REMOVED the onBlur from the form tag */}
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Node Name</FormLabel>
              <FormControl>
                <Input placeholder="MCP Tool" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="toolEndpoint"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Tool Endpoint URL</FormLabel>
              <FormControl>
                <Input placeholder="http://localhost:8080/mcp/" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        {/* ADDED the explicit Save button */}
        <Button type="submit" className="w-full">Save Changes</Button>
      </form>
    </Form>
  )
}