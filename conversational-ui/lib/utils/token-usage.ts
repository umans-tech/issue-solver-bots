import 'server-only';

import { db } from '@/lib/db';
import { tokenUsage } from '@/lib/db/schema';

export interface TokenUsageData {
  messageId: string;
  provider: string;
  model: string;
  rawUsageData: any;
  providerMetadata?: any;
}

export async function recordTokenUsage(data: TokenUsageData) {
  try {
    return await db.insert(tokenUsage).values({
      messageId: data.messageId,
      provider: data.provider,
      model: data.model,
      rawUsageData: data.rawUsageData,
      providerMetadata: data.providerMetadata,
      createdAt: new Date(),
    });
  } catch (error) {
    console.error('Failed to record token usage:', error);
    // Don't throw - token usage tracking shouldn't break the chat flow
  }
}

export function extractProvider(model: string): string {
  // Extract provider from model string (e.g., "claude-3-5-sonnet-20241022" -> "anthropic")
  if (model.includes('claude') || model.includes('anthropic')) {
    return 'anthropic';
  } else if (model.includes('gpt') || model.includes('openai')) {
    return 'openai';
  } else if (model.includes('gemini') || model.includes('google')) {
    return 'google';
  } else {
    return 'unknown';
  }
}