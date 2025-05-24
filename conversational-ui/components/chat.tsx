'use client';

import type { Attachment, Message } from 'ai';
import { useChat } from '@ai-sdk/react';
import { useState, useEffect } from 'react';
import useSWR, { useSWRConfig } from 'swr';
import { useLocalStorage } from 'usehooks-ts';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';

import { ChatHeader } from '@/components/chat-header';
import type { Vote } from '@/lib/db/schema';
import { fetcher, generateUUID } from '@/lib/utils';
import { DEFAULT_CHAT_MODEL } from '@/lib/ai/models';

import { Artifact } from './artifact';
import { MultimodalInput } from './multimodal-input';
import { Messages } from './messages';
import { VisibilityType } from './visibility-selector';
import { useArtifactSelector } from '@/hooks/use-artifact';

export function Chat({
  id,
  initialMessages,
  selectedChatModel,
  selectedVisibilityType,
  isReadonly,
  autoResume,
}: {
  id: string;
  initialMessages: Array<Message>;
  selectedChatModel: string;
  selectedVisibilityType: VisibilityType;
  isReadonly: boolean;
  autoResume: boolean;
}) {
  const { mutate } = useSWRConfig();
  const [storedModelId] = useLocalStorage('chat-model', selectedChatModel);
  const router = useRouter();
  const { data: session } = useSession();
  
  // Handle potential corrupt localStorage data
  const [knowledgeBaseIdState, setKnowledgeBaseIdState] = useState<string | null>(null);
  
  useEffect(() => {
    // Safely get the knowledge base ID from localStorage
    try {
      const rawValue = localStorage.getItem('knowledge_base_id');
      // If the value is a raw string (not JSON), use it directly
      if (rawValue && (rawValue.startsWith('"') || rawValue.startsWith('{'))) {
        // Attempt to parse JSON
        try {
          const parsedValue = JSON.parse(rawValue);
          setKnowledgeBaseIdState(parsedValue);
        } catch (e) {
          console.error('Error parsing knowledge_base_id from localStorage:', e);
          // Clear invalid data
          localStorage.removeItem('knowledge_base_id');
        }
      } else if (rawValue) {
        // Treat as a raw string value (not JSON)
        setKnowledgeBaseIdState(rawValue);
      }
    } catch (e) {
      console.error('Error reading knowledge_base_id from localStorage:', e);
    }
  }, []);

  const {
    messages,
    setMessages,
    handleSubmit,
    input,
    setInput,
    append,
    isLoading,
    stop,
    reload,
    experimental_resume,
  } = useChat({
    id,
    body: { 
      id, 
      selectedChatModel: storedModelId || DEFAULT_CHAT_MODEL,
      knowledgeBaseId: knowledgeBaseIdState,
    },
    initialMessages,
    experimental_throttle: 100,
    sendExtraMessageFields: true,
    generateId: generateUUID,
    onFinish: () => {
      mutate('/api/history');
    },
    onError: (error) => {
      console.error('Error in useChat:\n', error.message);
      console.error('Call stack:\n', error.stack);
      toast.error('An error occured, please try again!');
    },
  });

  useEffect(() => {
    if (autoResume) {
      experimental_resume();
    }

    // note: this hook has no dependencies since it only needs to run once
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);


  const { data: votes } = useSWR<Array<Vote>>(
    `/api/vote?chatId=${id}`,
    fetcher,
  );

  const [attachments, setAttachments] = useState<Array<Attachment>>([]);
  const isArtifactVisible = useArtifactSelector((state) => state.isVisible);

  return (
    <>
      <div className="flex flex-col min-w-0 h-dvh bg-background">
        <ChatHeader
          chatId={id}
          selectedVisibilityType={selectedVisibilityType}
          isReadonly={isReadonly}
        />

        <Messages
          chatId={id}
          isLoading={isLoading}
          votes={votes}
          messages={messages}
          setMessages={setMessages}
          reload={reload}
          isReadonly={isReadonly}
          isArtifactVisible={isArtifactVisible}
        />

        <form className="flex mx-auto px-4 bg-background pb-4 md:pb-6 gap-2 w-full md:max-w-3xl">
          {!isReadonly && (
            <MultimodalInput
              chatId={id}
              input={input}
              setInput={setInput}
              handleSubmit={handleSubmit}
              isLoading={isLoading}
              stop={stop}
              attachments={attachments}
              setAttachments={setAttachments}
              messages={messages}
              setMessages={setMessages}
              append={append}
              selectedModelId={storedModelId || DEFAULT_CHAT_MODEL}
            />
          )}
          {isReadonly && (
            <div className="w-full flex justify-center items-center">
              <Button
                variant="outline"
                onClick={async (e) => {
                  e.preventDefault();
                  
                  // Check if user is authenticated
                  if (!session?.user) {
                    toast.error('Please sign in to continue this conversation');
                    return;
                  }
                  
                  try {
                    // Call branch API with the last message ID
                    const lastMessage = messages[messages.length - 1];
                    const response = await fetch('/api/branch', {
                      method: 'POST',
                      headers: {
                        'Content-Type': 'application/json',
                      },
                      body: JSON.stringify({
                        sourceChatId: id,
                        messageId: lastMessage.id,
                      }),
                    });
                    
                    if (!response.ok) {
                      throw new Error('Failed to create conversation copy');
                    }
                    
                    const data = await response.json();
                    if (data.success && data.newChatId) {
                      toast.success('Created new conversation from shared chat!');
                      // Navigate to the new chat
                      router.push(`/chat/${data.newChatId}`);
                    }
                  } catch (error) {
                    console.error('Error continuing conversation:', error);
                    toast.error('Failed to create conversation copy');
                  }
                }}
              >
                Continue this conversation
              </Button>
            </div>
          )}
        </form>
      </div>

      <Artifact
        chatId={id}
        input={input}
        setInput={setInput}
        handleSubmit={handleSubmit}
        isLoading={isLoading}
        stop={stop}
        attachments={attachments}
        setAttachments={setAttachments}
        append={append}
        messages={messages}
        setMessages={setMessages}
        reload={reload}
        votes={votes}
        isReadonly={isReadonly}
        selectedModelId={storedModelId || DEFAULT_CHAT_MODEL}
      />
    </>
  );
}
