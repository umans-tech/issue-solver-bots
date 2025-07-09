import 'server-only';

import { saveTokenUsage as saveTokenUsageQuery } from '@/lib/db/queries';

export interface TokenUsageData {
  chatId: string;
  userId: string;
  spaceId?: string;
  model: string;
  provider: string;
  promptTokens?: number;
  completionTokens?: number;
  totalTokens?: number;
  reasoningTokens?: number;
  thinkingTokens?: number;
  thinkingBudgetTokens?: number;
  cachedTokens?: number;
  cacheCreationTokens?: number;
  cacheReadTokens?: number;
  rawUsageData?: any;
}

/**
 * Extract token usage data from AI SDK experimental telemetry
 */
export function extractTokenUsage(
  telemetryData: any,
  chatId: string,
  userId: string,
  spaceId?: string,
  model?: string,
  provider?: string
): TokenUsageData | null {
  if (!telemetryData || !telemetryData.usage) {
    return null;
  }

  const usage = telemetryData.usage;
  
  // Extract provider from model if not provided
  const inferredProvider = provider || inferProviderFromModel(model || '');
  
  // Base usage data
  const baseUsage: TokenUsageData = {
    chatId,
    userId,
    spaceId,
    model: model || 'unknown',
    provider: inferredProvider,
    promptTokens: usage.promptTokens,
    completionTokens: usage.completionTokens,
    totalTokens: usage.totalTokens,
    rawUsageData: usage,
  };

  // Provider-specific token extraction
  switch (inferredProvider) {
    case 'openai':
      return extractOpenAITokens(usage, baseUsage);
    
    case 'anthropic':
      return extractAnthropicTokens(usage, baseUsage);
    
    case 'google':
      return extractGoogleTokens(usage, baseUsage);
    
    default:
      return baseUsage;
  }
}

/**
 * Extract OpenAI-specific token usage including reasoning tokens
 */
function extractOpenAITokens(usage: any, baseUsage: TokenUsageData): TokenUsageData {
  return {
    ...baseUsage,
    reasoningTokens: usage.reasoningTokens,
    cachedTokens: usage.cachedTokens,
    cacheCreationTokens: usage.cacheCreationTokens,
    cacheReadTokens: usage.cacheReadTokens,
  };
}

/**
 * Extract Anthropic-specific token usage including thinking tokens
 */
function extractAnthropicTokens(usage: any, baseUsage: TokenUsageData): TokenUsageData {
  return {
    ...baseUsage,
    thinkingTokens: usage.thinkingTokens,
    thinkingBudgetTokens: usage.thinkingBudgetTokens,
    cachedTokens: usage.cachedTokens,
    cacheCreationTokens: usage.cacheCreationTokens,
    cacheReadTokens: usage.cacheReadTokens,
  };
}

/**
 * Extract Google-specific token usage
 */
function extractGoogleTokens(usage: any, baseUsage: TokenUsageData): TokenUsageData {
  return {
    ...baseUsage,
    cachedTokens: usage.cachedTokens,
  };
}

/**
 * Infer provider from model name
 */
function inferProviderFromModel(model: string): string {
  const modelLower = model.toLowerCase();
  
  if (modelLower.includes('gpt') || modelLower.includes('o1') || modelLower.includes('openai')) {
    return 'openai';
  }
  
  if (modelLower.includes('claude') || modelLower.includes('anthropic')) {
    return 'anthropic';
  }
  
  if (modelLower.includes('gemini') || modelLower.includes('google')) {
    return 'google';
  }
  
  return 'unknown';
}

/**
 * Save token usage data to database
 */
export async function saveTokenUsage(usageData: TokenUsageData): Promise<void> {
  try {
    await saveTokenUsageQuery(usageData);
  } catch (error) {
    console.error('Failed to save token usage:', error);
    throw error;
  }
}

/**
 * Record token usage from AI SDK telemetry data
 */
export async function recordTokenUsage(
  telemetryData: any,
  chatId: string,
  userId: string,
  spaceId?: string,
  model?: string,
  provider?: string
): Promise<void> {
  const usageData = extractTokenUsage(telemetryData, chatId, userId, spaceId, model, provider);
  
  if (usageData) {
    await saveTokenUsage(usageData);
  }
}