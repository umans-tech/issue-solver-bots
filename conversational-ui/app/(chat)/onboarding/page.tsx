import { auth } from '@/app/(auth)/auth';
import { Chat } from '@/components/chat';
import { DEFAULT_CHAT_MODEL } from '@/lib/ai/models';
import { generateUUID } from '@/lib/utils';
import { DataStreamHandler } from '@/components/data-stream-handler';
import { saveChat, saveMessages, getCurrentUserSpace } from '@/lib/db/queries';
import { UIMessage } from 'ai';
import { redirect } from 'next/navigation';

export const dynamic = 'force-dynamic';

export default async function OnboardingPage() {
  const session = await auth();
  
  if (!session?.user?.id) {
    redirect('/login');
  }

  // Check if user has already completed onboarding
  if ((session.user as any).hasCompletedOnboarding) {
    redirect('/');
  }

  const id = generateUUID();
  
  // Get current user's selected space
  const currentSpace = await getCurrentUserSpace(session.user.id);
  if (!currentSpace) {
    throw new Error('Unable to determine user space');
  }

  // Create the chat
  await saveChat({ 
    id, 
    userId: session.user.id, 
    title: 'Onboarding',
    spaceId: currentSpace.id
  });

  // Create the initial AI welcome message
  const userName = session.user.name;
  const welcomeText = userName 
    ? `Hi there! Welcome to umans.ai! 👋\n\nI'd like to make sure I'm addressing you correctly - should I call you ${userName}, or would you prefer something else?`
    : `Hi there! Welcome to umans.ai! 👋\n\nWhat would you like me to call you?`;
  
  const welcomeMessage: UIMessage = {
    id: generateUUID(),
    role: 'assistant',
    content: welcomeText,
    parts: [{
      type: 'text',
      text: welcomeText
    }],
    createdAt: new Date(),
  };

  // Save the welcome message to the database
  await saveMessages({
    messages: [{
      id: welcomeMessage.id,
      chatId: id,
      role: 'assistant',
      parts: welcomeMessage.parts,
      attachments: [],
      createdAt: new Date(),
    }]
  });

  return (
    <>
      <Chat
        id={id}
        initialMessages={[welcomeMessage]}
        selectedChatModel={DEFAULT_CHAT_MODEL}
        selectedVisibilityType="private"
        isReadonly={false}
        autoResume={false}
      />
      <DataStreamHandler id={id} />
    </>
  );
} 