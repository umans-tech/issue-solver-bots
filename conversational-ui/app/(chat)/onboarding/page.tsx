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
  const welcomeMessage: UIMessage = {
    id: generateUUID(),
    role: 'assistant',
    content: "Hi there! Welcome to umans.ai! 👋 I'm excited to help you get the most out of our platform.\n\nTo start, I'd love to know a bit about you - what's your role in software development?",
    parts: [{
      type: 'text',
      text: "Hi there! Welcome to umans.ai! 👋 I'm excited to help you get the most out of our platform.\n\nTo start, I'd love to know a bit about you - what's your role in software development?"
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