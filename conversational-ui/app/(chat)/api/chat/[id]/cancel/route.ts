import { auth } from '@/app/(auth)/auth';
import { getChatById, getStreamIdsByChatId } from '@/lib/db/queries';
import type { Chat } from '@/lib/db/schema';
import { getController, deleteController } from '@/lib/stream/controller-registry';

export async function POST(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id: chatId } = await params;

  if (!chatId) return new Response('id is required', { status: 400 });

  const session = await auth();
  let chat: Chat | undefined;
  try {
    chat = await getChatById({ id: chatId });
  } catch {
    return new Response(null, { status: 204 });
  }

  if (!chat) return new Response(null, { status: 204 });

  // Only owner can cancel private chats; public chats require auth
  if (chat.visibility !== 'public' && !session?.user) {
    return new Response('Unauthorized', { status: 401 });
  }
  if (chat.visibility === 'private' && chat.userId !== session?.user?.id) {
    return new Response('Forbidden', { status: 403 });
  }

  const streamIds = await getStreamIdsByChatId({ chatId });
  const recentStreamId = streamIds.at(-1);
  if (!recentStreamId) return new Response(null, { status: 204 });

  const controller = getController(recentStreamId);
  if (!controller) return new Response(null, { status: 204 });

  try {
    controller.abort();
  } finally {
    deleteController(recentStreamId);
  }

  return new Response(null, { status: 200 });
}

