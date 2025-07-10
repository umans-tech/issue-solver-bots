import 'server-only';

import { tokenUsage } from '@/lib/db/schema';
import { db } from '@/lib/db';

export interface RecordTokenUsageParams {
  userId: string;
  spaceId: string;
  messageId: string;
  chatId: string;
  provider: string;
  model: string;
  operationType: string;
  operationId?: string;
  rawUsageData: Record<string, any>;
  providerMetadata?: Record<string, any>;
  finishReason?: string;
  requestId?: string;
}

export interface TokenUsageFromTelemetry {
  provider: string;
  model: string;
  operationType: string;
  operationId?: string;
  rawUsageData: Record<string, any>;
  providerMetadata?: Record<string, any>;
  finishReason?: string;
  requestId?: string;
}

/**
 * Records token usage data to the database
 * Stores raw usage data and provider metadata for comprehensive tracking
 */
export async function recordTokenUsage(params: RecordTokenUsageParams): Promise<void> {
  try {
    await db.insert(tokenUsage).values({
      userId: params.userId,
      spaceId: params.spaceId,
      messageId: params.messageId,
      chatId: params.chatId,
      provider: params.provider,
      model: params.model,
      operationType: params.operationType,
      operationId: params.operationId,
      rawUsageData: params.rawUsageData,
      providerMetadata: params.providerMetadata,
      finishReason: params.finishReason,
      requestId: params.requestId,
      createdAt: new Date(),
    });
  } catch (error) {
    console.error('Failed to record token usage:', error);
    // Don't throw to avoid breaking the chat flow
  }
}

/**
 * Extracts token usage data from AI SDK telemetry data
 */
export function extractTokenUsageFromTelemetry(telemetryData: any): TokenUsageFromTelemetry | null {
  try {
    if (!telemetryData || !telemetryData.usage) {
      console.log('No usage data found in telemetry:', telemetryData);
      return null;
    }

    // Extract provider information from model metadata or default
    const provider = telemetryData.model?.provider || telemetryData.provider || 'unknown';
    const modelName = telemetryData.model?.modelId || telemetryData.model || 'unknown';
    
    return {
      provider,
      model: modelName,
      operationType: telemetryData.operationType || 'generate',
      operationId: telemetryData.operationId,
      rawUsageData: {
        usage: telemetryData.usage,
        timestamp: telemetryData.timestamp || new Date().toISOString(),
        durationMs: telemetryData.durationMs,
      },
      providerMetadata: {
        model: telemetryData.model,
        settings: telemetryData.settings,
        response: telemetryData.response,
      },
      finishReason: telemetryData.response?.finishReason,
      requestId: telemetryData.response?.id || telemetryData.requestId,
    };
  } catch (error) {
    console.error('Failed to extract token usage from telemetry:', error);
    return null;
  }
}