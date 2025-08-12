// src/components/panels/forms/LLMNodeForm.tsx
"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { LLMNodeSchema, OPENAI_MODELS, GOOGLE_MODELS } from "@/lib/schemas"
import { useWorkflowStore } from "@/store/workflow-store"
import { Node } from "reactflow"
import { useEffect } from "react"
import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Slider } from "@/components/ui/slider"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

type LLMFormValues = z.infer<typeof LLMNodeSchema>

// Define our standard credential names
const CREDENTIAL_NAMES = {
  openai: "OPENAI_API_KEY",
  google_genai: "GOOGLE_API_KEY",
};

interface LLMNodeFormProps {
  node: Node;
}

export function LLMNodeForm({ node }: LLMNodeFormProps) {
  const updateNodeParams = useWorkflowStore((state) => state.updateNodeParams)

  const form = useForm<LLMFormValues>({
    resolver: zodResolver(LLMNodeSchema),
    defaultValues: {
      name: node.data.name || "LLM Agent",
      modelProvider: node.data.params?.modelProvider || "openai",
      model: node.data.params?.model || "gpt-4o-mini",
      apiKeyName: node.data.params?.apiKeyName || CREDENTIAL_NAMES.openai, // Default to the standard name
      temperature: node.data.params?.temperature === undefined ? 0.7 : node.data.params.temperature,
      systemPrompt: node.data.params?.systemPrompt || "",
    },
  })
  
  const watchedProvider = form.watch("modelProvider");

  // This effect now also updates the credential name automatically
  useEffect(() => {
    const { setValue } = form;
    if (watchedProvider === 'openai') {
        setValue('model', OPENAI_MODELS[0]);
        setValue('apiKeyName', CREDENTIAL_NAMES.openai);
    } else if (watchedProvider === 'google_genai') {
        setValue('model', GOOGLE_MODELS[0]);
        setValue('apiKeyName', CREDENTIAL_NAMES.google_genai);
    } else if (watchedProvider === 'self-hosted') {
        setValue('model', '');
        setValue('apiKeyName', ''); // No key needed for self-hosted
    }
  }, [watchedProvider, form]);

  function onSubmit(values: LLMFormValues) {
    updateNodeParams(node.id, values)
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        {/* Node Name Field */}
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Node Name</FormLabel>
              <FormControl><Input placeholder="LLM Agent" {...field} /></FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        {/* Model Provider Field */}
        <FormField
          control={form.control}
          name="modelProvider"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Model Provider</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl>
                  <SelectTrigger><SelectValue placeholder="Select a provider" /></SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="openai">OpenAI</SelectItem>
                  <SelectItem value="google_genai">Google</SelectItem>
                  <SelectItem value="self-hosted">Self-Hosted</SelectItem>
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />
        
        {/* --- API KEY CREDENTIAL DROPDOWN --- */}
        {watchedProvider !== 'self-hosted' && (
          <FormField
            control={form.control}
            name="apiKeyName"
            key={`${watchedProvider}-key`} // Add key to force re-render
            render={({ field }) => (
              <FormItem>
                <FormLabel>API Key Credential</FormLabel>
                {/* It's now a dropdown, pre-filled based on the provider */}
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                    </FormControl>
                    <SelectContent>
                        {watchedProvider === 'openai' && <SelectItem value={CREDENTIAL_NAMES.openai}>{CREDENTIAL_NAMES.openai}</SelectItem>}
                        {watchedProvider === 'google_genai' && <SelectItem value={CREDENTIAL_NAMES.google_genai}>{CREDENTIAL_NAMES.google_genai}</SelectItem>}
                    </SelectContent>
                </Select>
                <FormDescription>
                  Your backend will use this environment variable.
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        )}
        
        {/* Model Name Field */}
        <FormField
          control={form.control}
          name="model"
          key={watchedProvider} 
          render={({ field }) => (
            <FormItem>
              <FormLabel>Model Name</FormLabel>
                {watchedProvider === 'openai' && (
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl><SelectTrigger><SelectValue placeholder="Select a model" /></SelectTrigger></FormControl>
                    <SelectContent>{OPENAI_MODELS.map(model => <SelectItem key={model} value={model}>{model}</SelectItem>)}</SelectContent>
                  </Select>
                )}
                {watchedProvider === 'google_genai' && (
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl><SelectTrigger><SelectValue placeholder="Select a model" /></SelectTrigger></FormControl>
                    <SelectContent>{GOOGLE_MODELS.map(model => <SelectItem key={model} value={model}>{model}</SelectItem>)}</SelectContent>
                  </Select>
                )}
                {watchedProvider === 'self-hosted' && (
                   <FormControl><Input placeholder="e.g., Llama-3-70b-Instruct" {...field} /></FormControl>
                )}
              <FormDescription>
                {watchedProvider === 'self-hosted' ? "Specify the full model name." : "Select a model from the list."}
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        
        {/* System Prompt & Temperature Fields ... */}
        <FormField
          control={form.control}
          name="systemPrompt"
          render={({ field }) => (
            <FormItem>
              <FormLabel>System Prompt</FormLabel>
              <FormControl><Textarea placeholder="You are a helpful assistant." className="resize-none" {...field} /></FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="temperature"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Temperature: {field.value}</FormLabel>
              <FormControl><Slider min={0} max={2} step={0.1} defaultValue={[field.value]} onValueChange={(value) => field.onChange(value[0])} /></FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <Button type="submit" className="w-full">Save Changes</Button>
      </form>
    </Form>
  )
}