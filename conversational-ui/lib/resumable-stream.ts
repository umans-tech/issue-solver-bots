import { createResumableStreamConsumer, createResumableStreamPublisher } from 'resumable-stream';
import { getRedis } from './redis/client';
import { saveChatStream, updateChatStream, getLatestChatStreamByChatId } from './db/queries';

/**
 * Creates a resumable stream publisher for a chat
 * 
 * @param chatId The chat ID
 * @param existingStreamId Optional existing stream ID to update
 * @returns The resumable stream publisher and stream ID
 */
export async function createResumableStreamPublisher(chatId: string, existingStreamId?: string) {
  const redis = getRedis();
  if (!redis) {
    console.warn('Redis client not available. Resumable streams disabled.');
    return { publisher: null, streamId: null };
  }

  try {
    const streamId = existingStreamId || crypto.randomUUID();
    const publisher = createResumableStreamPublisher({
      streamId,
      storage: {
        async set(key, value) {
          await redis.set(key, value);
        },
        async get(key) {
          return await redis.get(key);
        },
      },
    });

    // Save or update the stream in the database
    if (existingStreamId) {
      const latestStream = await getLatestChatStreamByChatId({ chatId });
      if (latestStream) {
        await updateChatStream({ id: latestStream.id, streamId });
      } else {
        await saveChatStream({ chatId, streamId });
      }
    } else {
      await saveChatStream({ chatId, streamId });
    }

    return { publisher, streamId };
  } catch (error) {
    console.error('Error creating resumable stream publisher:', error);
    return { publisher: null, streamId: null };
  }
}

/**
 * Creates a resumable stream consumer for a chat
 * 
 * @param streamId The stream ID to consume
 * @returns The resumable stream consumer or null if not available
 */
export async function createResumableStreamConsumer(streamId: string) {
  const redis = getRedis();
  if (!redis) {
    console.warn('Redis client not available. Resumable streams disabled.');
    return null;
  }

  try {
    return createResumableStreamConsumer({
      streamId,
      storage: {
        async get(key) {
          return await redis.get(key);
        },
      },
    });
  } catch (error) {
    console.error('Error creating resumable stream consumer:', error);
    return null;
  }
}

/**
 * Gets the latest stream ID for a chat
 * 
 * @param chatId The chat ID
 * @returns The latest stream ID or null if not found
 */
export async function getLatestStreamId(chatId: string) {
  try {
    const latestStream = await getLatestChatStreamByChatId({ chatId });
    return latestStream ? latestStream.streamId : null;
  } catch (error) {
    console.error('Error getting latest stream ID:', error);
    return null;
  }
}