// src/lib/schemas.ts
import { z } from "zod";

export const OPENAI_MODELS = ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1-nano", "o4-mini", "o3-mini", "gpt-4.1", "gpt-4o"] as const;
export const GOOGLE_MODELS = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"] as const;

// Shared schema for all nodes that have a name
export const NodeNameSchema = z.object({
  name: z.string().min(1, { message: "Name is required." }),
});

// Schema for LLMNode parameters
export const LLMNodeSchema = NodeNameSchema.extend({
  modelProvider: z.enum(["openai", "google_genai", "self-hosted"]),
  model: z.string().min(1, { message: "Model is required." }),
  apiKeyName: z.string().optional(), // We use a reference to the key, not the key itself
  temperature: z.number().min(0).max(2.0),
  systemPrompt: z.string().optional(),
});

// Schema for ToolNode parameters
export const ToolNodeSchema = NodeNameSchema.extend({
  toolEndpoint: z.string().url({ message: "Must be a valid URL." }),
});

// Schema for A2ANode parameters
export const A2ANodeSchema = NodeNameSchema.extend({
  apiBaseUrl: z.string().url({ message: "Must be a valid URL." }),
});