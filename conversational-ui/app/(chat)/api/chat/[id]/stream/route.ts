import { auth } from '@/app/(auth)/auth';
import {
  getChatById,
  getMessagesByChatId,
  getStreamIdsByChatId,
} from '@/lib/db/queries';
import type { Chat } from '@/lib/db/schema';
import { createUIMessageStream, JsonToSseTransformStream } from 'ai';
import { getStreamContext } from '../../route';
import { differenceInSeconds } from 'date-fns';
import type { ChatMessage } from '@/lib/types';

export async function GET(
    _: Request,
    { params }: { params: Promise<{ id: string }> },
  ) {
    const { id: chatId } = await params;
    const streamContext = getStreamContext();
    const resumeRequestedAt = new Date();

    if (!streamContext) {
      return new Response(null, { status: 204 });
    }

    if (!chatId) {
      return new Response('id is required', { status: 400 });
    }

    const session = await auth();

    let chat: Chat;

    try {
      chat = await getChatById({ id: chatId });
    } catch {
      return new Response('Not found', { status: 404 });
    }

    if (!chat) {
      return new Response('Not found', { status: 404 });
    }

    if (chat.visibility !== 'public' && !session?.user) {
      return new Response('Unauthorized', { status: 401 });
    }

    if (chat.visibility === 'private' && chat.userId !== session?.user.id) {
      return new Response('Forbidden', { status: 403 });
    }

    const streamIds = await getStreamIdsByChatId({ chatId });

    // If this chat has no recorded streams, respond with 204 (No Content)
    // to avoid client-side errors while keeping resume a no-op.
    if (!streamIds.length) {
      return new Response(null, { status: 204 });
    }

    const recentStreamId = streamIds.at(-1);

    if (!recentStreamId) {
      return new Response(null, { status: 204 });
    }

    const emptyDataStream = createUIMessageStream<ChatMessage>({
        execute: () => {},
    });

    const stream = await streamContext.resumableStream(recentStreamId, () =>
        emptyDataStream.pipeThrough(new JsonToSseTransformStream()),
    );

    /*
     * For when the generation is streaming during SSR
     * but the resumable stream has concluded at this point.
     */
    if (!stream) {
      const messages = await getMessagesByChatId({ id: chatId });
      const mostRecentMessage = messages.at(-1);

      if (!mostRecentMessage) {
        return new Response(emptyDataStream, { status: 200 });
      }

      if (mostRecentMessage.role !== 'assistant') {
        return new Response(emptyDataStream, { status: 200 });
      }

      const messageCreatedAt = new Date(mostRecentMessage.createdAt);

      if (differenceInSeconds(resumeRequestedAt, messageCreatedAt) > 15) {
        return new Response(emptyDataStream, { status: 200 });
      }

      const restoredStream = createUIMessageStream<ChatMessage>({
        execute: ({ writer }) => {
          writer.write({
            type: 'data-appendMessage',
            data: JSON.stringify(mostRecentMessage),
            transient: true,
          });
        },
      });

      return new Response(restoredStream.pipeThrough(new JsonToSseTransformStream()), { status: 200 });
    }

    return new Response(stream, { status: 200 });
  }
