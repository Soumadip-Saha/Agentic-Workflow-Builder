// src/components/panels/forms/A2ANodeForm.tsx
"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { A2ANodeSchema } from "@/lib/schemas"
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

type A2AFormValues = z.infer<typeof A2ANodeSchema>

interface A2ANodeFormProps {
  node: Node;
}

export function A2ANodeForm({ node }: A2ANodeFormProps) {
  const updateNodeParams = useWorkflowStore((state) => state.updateNodeParams)

  const form = useForm<A2AFormValues>({
    resolver: zodResolver(A2ANodeSchema),
    defaultValues: {
      name: node.data.name || "A2A Agent",
      apiBaseUrl: node.data.params?.apiBaseUrl || "",
    },
  })

  function onSubmit(values: A2AFormValues) {
    updateNodeParams(node.id, values)
    // Optional: Add a "toast" notification here to show it saved
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
                <Input placeholder="A2A Agent" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="apiBaseUrl"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Agent API Base URL</FormLabel>
              <FormControl>
                <Input placeholder="http://localhost:10000" {...field} />
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