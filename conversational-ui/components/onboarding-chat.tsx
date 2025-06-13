'use client';

import { UIMessage } from 'ai';
import { Chat } from '@/components/chat';
import { DEFAULT_CHAT_MODEL } from '@/lib/ai/models';
import { generateUUID } from '@/lib/utils';
import { DataStreamHandler } from '@/components/data-stream-handler';

export function OnboardingChat() {
  const id = generateUUID();
  
  const onboardingMessage: UIMessage = {
    id: generateUUID(),
    role: 'assistant',
    content: '',
    parts: [{
      type: 'text',
      text: `Hi! I'm your AI assistant from umans.ai. I'm here to help you get familiar with our platform and understand how I can best support your team.

Let's start with a few questions to get to know you better:

• What's your role in software development?
• What kind of challenges is your team currently facing?
• Have you used AI assistants for development work before?

Feel free to share as much or as little as you'd like - we can explore the platform together! 🚀`
    }],
    createdAt: new Date(),
  };

  return (
    <>
      <Chat
        id={id}
        initialMessages={[onboardingMessage]}
        selectedChatModel={DEFAULT_CHAT_MODEL}
        selectedVisibilityType="private"
        isReadonly={false}
        autoResume={false}
      />
      <DataStreamHandler id={id} />
    </>
  );
} 