import 'server-only';

import { db } from '@/lib/db';
import { tokenUsage } from '@/lib/db/schema';
import { myProvider } from '@/lib/ai/models';

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

export function extractModel(selectedChatModel: string) {
  const languageModel = myProvider.languageModel(selectedChatModel);
  if (!languageModel) {
    // Don't throw - token usage tracking shouldn't break the chat flow
    console.error(`Language model not found for: ${selectedChatModel}`);
  }
  return {
    chatModelProvider: languageModel.provider,
    chatModelName: languageModel.modelId,
  };
}
