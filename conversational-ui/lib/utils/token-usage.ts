import 'server-only';
import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import { tokenUsage } from '../db/schema';
import type { TokenUsage } from '../db/schema';

// AI SDK telemetry types
export interface TelemetryUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
}

export interface TelemetryData {
  usage?: TelemetryUsage;
  experimental_providerMetadata?: {
    anthropic?: {
      cacheCreationInputTokens?: number;
      cacheReadInputTokens?: number;
      [key: string]: any;
    };
    openai?: {
      reasoning_tokens?: number;
      [key: string]: any;
    };
    google?: {
      [key: string]: any;
    };
    [key: string]: any;
  };
}

// Cost calculation utilities (in microdollars)
const MODEL_COSTS = {
  // OpenAI GPT-4 models (per 1K tokens)
  'gpt-4o': { input: 2500, output: 10000 }, // $0.0025 input, $0.01 output
  'gpt-4o-mini': { input: 150, output: 600 }, // $0.00015 input, $0.0006 output
  'gpt-4-turbo': { input: 10000, output: 30000 }, // $0.01 input, $0.03 output
  'gpt-4': { input: 30000, output: 60000 }, // $0.03 input, $0.06 output
  'gpt-3.5-turbo': { input: 500, output: 1500 }, // $0.0005 input, $0.0015 output
  
  // Anthropic Claude models (per 1K tokens)
  'claude-3-5-sonnet-20241022': { input: 3000, output: 15000 }, // $0.003 input, $0.015 output
  'claude-3-5-haiku-20241022': { input: 1000, output: 5000 }, // $0.001 input, $0.005 output
  'claude-3-opus-20240229': { input: 15000, output: 75000 }, // $0.015 input, $0.075 output
  'claude-3-sonnet-20240229': { input: 3000, output: 15000 }, // $0.003 input, $0.015 output
  'claude-3-haiku-20240307': { input: 250, output: 1250 }, // $0.00025 input, $0.00125 output
  
  // Google Gemini models (per 1K tokens)
  'gemini-1.5-pro': { input: 2500, output: 10000 }, // $0.0025 input, $0.01 output
  'gemini-1.5-flash': { input: 75, output: 300 }, // $0.000075 input, $0.0003 output
} as const;

function extractProviderAndModel(fullModelName: string): { provider: string; model: string } {
  // Handle provider-prefixed models (e.g., "openai:gpt-4o")
  if (fullModelName.includes(':')) {
    const [provider, model] = fullModelName.split(':', 2);
    return { provider, model };
  }
  
  // Infer provider from model name patterns
  if (fullModelName.startsWith('gpt-')) {
    return { provider: 'openai', model: fullModelName };
  }
  
  if (fullModelName.startsWith('claude-')) {
    return { provider: 'anthropic', model: fullModelName };
  }
  
  if (fullModelName.startsWith('gemini-')) {
    return { provider: 'google', model: fullModelName };
  }
  
  // Default fallback
  return { provider: 'unknown', model: fullModelName };
}

function calculateCost(model: string, promptTokens: number, completionTokens: number): {
  inputCost: number;
  outputCost: number;
  totalCost: number;
} {
  const costs = MODEL_COSTS[model as keyof typeof MODEL_COSTS];
  
  if (!costs) {
    return { inputCost: 0, outputCost: 0, totalCost: 0 };
  }
  
  // Calculate costs in microdollars
  const inputCost = Math.round((promptTokens / 1000) * costs.input);
  const outputCost = Math.round((completionTokens / 1000) * costs.output);
  const totalCost = inputCost + outputCost;
  
  return { inputCost, outputCost, totalCost };
}

export interface TokenUsageRecord {
  messageId: string;
  chatId: string;
  provider: string;
  model: string;
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  inputCost?: number;
  outputCost?: number;
  totalCost?: number;
  providerMetadata?: any;
}

export function createTokenUsageRecord(
  messageId: string,
  chatId: string,
  modelName: string,
  telemetryData: TelemetryData
): TokenUsageRecord | null {
  // Early return if no usage data
  if (!telemetryData.usage) {
    console.warn('No usage data found in telemetry');
    return null;
  }
  
  const { usage, experimental_providerMetadata } = telemetryData;
  const { provider, model } = extractProviderAndModel(modelName);
  
  // Validate required fields
  if (!usage.promptTokens || !usage.completionTokens || !usage.totalTokens) {
    console.warn('Incomplete usage data in telemetry');
    return null;
  }
  
  // Calculate costs
  const { inputCost, outputCost, totalCost } = calculateCost(
    model,
    usage.promptTokens,
    usage.completionTokens
  );
  
  return {
    messageId,
    chatId,
    provider,
    model,
    promptTokens: usage.promptTokens,
    completionTokens: usage.completionTokens,
    totalTokens: usage.totalTokens,
    inputCost: inputCost > 0 ? inputCost : undefined,
    outputCost: outputCost > 0 ? outputCost : undefined,
    totalCost: totalCost > 0 ? totalCost : undefined,
    providerMetadata: experimental_providerMetadata || undefined,
  };
}

// Database connection
const client = postgres(process.env.POSTGRES_URL!);
const db = drizzle(client);

export async function saveTokenUsage(record: TokenUsageRecord): Promise<void> {
  try {
    await db.insert(tokenUsage).values({
      messageId: record.messageId,
      chatId: record.chatId,
      provider: record.provider,
      model: record.model,
      promptTokens: record.promptTokens,
      completionTokens: record.completionTokens,
      totalTokens: record.totalTokens,
      inputCost: record.inputCost,
      outputCost: record.outputCost,
      totalCost: record.totalCost,
      providerMetadata: record.providerMetadata,
    });
    
    console.log(`✅ Token usage recorded for message ${record.messageId}: ${record.totalTokens} tokens`);
  } catch (error) {
    console.error('❌ Failed to save token usage:', error);
    throw error;
  }
}

export async function recordTokenUsage(
  messageId: string,
  chatId: string,
  modelName: string,
  telemetryData: TelemetryData
): Promise<void> {
  const record = createTokenUsageRecord(messageId, chatId, modelName, telemetryData);
  
  if (!record) {
    console.warn('No token usage record created, skipping save');
    return;
  }
  
  await saveTokenUsage(record);
}

// Utility to format costs for display
export function formatCost(microdollars: number): string {
  const dollars = microdollars / 1_000_000;
  return `$${dollars.toFixed(6)}`;
}

// Type-safe telemetry data handler
export function handleTelemetryData(data: unknown): TelemetryData | null {
  if (!data || typeof data !== 'object') {
    return null;
  }
  
  const obj = data as Record<string, any>;
  
  // Validate usage object structure
  if (!obj.usage || typeof obj.usage !== 'object') {
    return null;
  }
  
  const usage = obj.usage as Record<string, any>;
  if (
    typeof usage.promptTokens !== 'number' ||
    typeof usage.completionTokens !== 'number' ||
    typeof usage.totalTokens !== 'number'
  ) {
    return null;
  }
  
  return {
    usage: {
      promptTokens: usage.promptTokens,
      completionTokens: usage.completionTokens,
      totalTokens: usage.totalTokens,
    },
    experimental_providerMetadata: obj.experimental_providerMetadata || undefined,
  };
}