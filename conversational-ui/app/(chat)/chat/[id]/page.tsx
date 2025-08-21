import { cookies } from 'next/headers';
import { notFound } from 'next/navigation';

import { auth } from '@/app/(auth)/auth';
import { Chat } from '@/components/chat';
import { getChatById, getMessagesByChatId, getStreamIdsByChatId } from '@/lib/db/queries';
import { DEFAULT_CHAT_MODEL } from '@/lib/ai/models';

import { convertToUIMessages } from '@/lib/utils';
import { DataStreamHandler } from '@/components/data-stream-handler';

export default async function Page(props: { params: Promise<{ id: string }> }) {
  const params = await props.params;
  const { id } = params;
  const chat = await getChatById({ id });

  if (!chat) {
    notFound();
  }

  const session = await auth();

  if (chat.visibility === 'private') {
    if (!session || !session.user) {
      return notFound();
    }

    if (session.user.id !== chat.userId) {
      return notFound();
    }
  }

  const messagesFromDb = await getMessagesByChatId({
    id,
  });

  const uiMessages = convertToUIMessages(messagesFromDb);

  // Check if this chat has any stream records before enabling autoResume
  const streamIds = await getStreamIdsByChatId({ chatId: id });
  const hasStreams = streamIds.length > 0;
  const shouldAutoResume = Boolean(session?.user && hasStreams);

  const cookieStore = await cookies();
  const chatModelFromCookie = cookieStore.get('chat-model');

  if (!chatModelFromCookie) {
    return (
      <>
      <Chat
        key={`${id}-${messagesFromDb.length}`}
        id={chat.id}
        initialMessages={uiMessages}
        selectedChatModel={DEFAULT_CHAT_MODEL}
        selectedVisibilityType={chat.visibility}
        isReadonly={session?.user?.id !== chat.userId}
        autoResume={shouldAutoResume}
      />
      <DataStreamHandler />
      </>
    );
  }

  return (
    <>
    <Chat
      key={`${id}-${messagesFromDb.length}`}
      id={chat.id}
      initialMessages={uiMessages}
      selectedChatModel={chatModelFromCookie.value}
      selectedVisibilityType={chat.visibility}
      isReadonly={session?.user?.id !== chat.userId}
      autoResume={shouldAutoResume}
    />
    <DataStreamHandler />
    </>
  );
}
