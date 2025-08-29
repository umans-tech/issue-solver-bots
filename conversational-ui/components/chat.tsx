'use client';

import { DefaultChatTransport } from 'ai';
import pRetry, { AbortError } from 'p-retry';
import { useChat } from '@ai-sdk/react';
import { useState, useEffect, useRef } from 'react';
import useSWR, { useSWRConfig } from 'swr';
import { useLocalStorage } from 'usehooks-ts';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';

import { ChatHeader } from '@/components/chat-header';
import type { Vote } from '@/lib/db/schema';
import { fetcher, generateUUID, fetchWithErrorHandlers } from '@/lib/utils';
import { DEFAULT_CHAT_MODEL } from '@/lib/ai/models';

import { Artifact } from './artifact';
import { MultimodalInput } from './multimodal-input';
import { Messages } from './messages';
import { VisibilityType } from './visibility-selector';
import { useArtifactSelector } from '@/hooks/use-artifact';
import { useAutoResume } from '@/hooks/use-auto-resume';
import { Attachment, ChatMessage } from '@/lib/types';
import { useDataStream } from '@/components/data-stream-provider';

export function Chat({
  id,
  initialMessages,
  selectedChatModel,
  selectedVisibilityType,
  isReadonly,
  autoResume,
}: {
  id: string;
  initialMessages: ChatMessage[];
  selectedChatModel: string;
  selectedVisibilityType: VisibilityType;
  isReadonly: boolean;
  autoResume: boolean;
}) {
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
  
  const { mutate } = useSWRConfig();
  const { setDataStream } = useDataStream();

  const [input, setInput] = useState<string>('');
  const [lastError, setLastError] = useState<unknown>(null);
  const retryCancelRef = useRef<boolean>(false);

  const isNetworkLikeError = (err: unknown) => {
    const message = err instanceof Error ? err.message : String(err);
    return /network|ERR_INCOMPLETE_CHUNKED_ENCODING|Failed to fetch|TypeError/i.test(message);
  };
  
  const {
    messages,
    setMessages,
    sendMessage,
    status,
    stop,
    regenerate,
    resumeStream,
  } = useChat<ChatMessage>({
    id,
    messages: initialMessages,
    experimental_throttle: 100,
    generateId: generateUUID,
    transport: new DefaultChatTransport({
      api: '/api/chat',
      fetch: fetchWithErrorHandlers,
      prepareSendMessagesRequest({ messages, id, body }) {
        return {
          body: {
            id,
            messages,
            selectedChatModel: storedModelId || DEFAULT_CHAT_MODEL,
            knowledgeBaseId: knowledgeBaseIdState,
            ...body,
          },
        };
      },
    }),
    onData: (dataPart) => {
      setDataStream((ds) => (ds ? [...ds, dataPart] : []));
    },
    onFinish: () => {
      mutate('/api/history');
    },
    onError: (error) => {
      setLastError(error);
      console.error('Error in useChat:\n', error.message);
      console.error('Call stack:\n', error.stack);
      if (!isNetworkLikeError(error)) {
        toast.error('An error occured, please try again!');
      }
    },
  });
  useEffect(() => {
    if (!lastError) return;
    if (!isNetworkLikeError(lastError)) return;

    retryCancelRef.current = false;

    // Attempt resumable continuation with bounded retries and backoff.
    void pRetry(() => {
      if (retryCancelRef.current) {
        throw new AbortError('resume cancelled');
      }
      return Promise.resolve(resumeStream());
    }, {
      retries: 3,
      factor: 2,
      minTimeout: 800,
      maxTimeout: 3000,
      randomize: true,
    }).catch(() => {});
    
    return () => {
      retryCancelRef.current = true;
    };
  }, [lastError, resumeStream]);



  const { data: votes } = useSWR<Array<Vote>>(
    `/api/vote?chatId=${id}`,
    fetcher,
  );

  const [attachments, setAttachments] = useState<Array<Attachment>>([]);
  const isArtifactVisible = useArtifactSelector((state) => state.isVisible);

  useAutoResume({
    autoResume,
    initialMessages,
    resumeStream,
    setMessages,
  });

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
          status={status}
          votes={votes}
          messages={messages}
          setMessages={setMessages}
          regenerate={regenerate}
          isReadonly={isReadonly}
          isArtifactVisible={isArtifactVisible}
          selectedChatModel={storedModelId || DEFAULT_CHAT_MODEL}
        />

        <form className="flex mx-auto px-4 bg-background pb-4 md:pb-6 gap-2 w-full md:max-w-3xl">
          {!isReadonly && (
            <MultimodalInput
              chatId={id}
              input={input}
              setInput={setInput}
              status={status}
              stop={stop}
              attachments={attachments}
              setAttachments={setAttachments}
              messages={messages}
              setMessages={setMessages}
              sendMessage={sendMessage}
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
        status={status}
        stop={stop}
        attachments={attachments}
        setAttachments={setAttachments}
        sendMessage={sendMessage}
        messages={messages}
        setMessages={setMessages}
        regenerate={regenerate}
        votes={votes}
        isReadonly={isReadonly}
        selectedModelId={storedModelId || DEFAULT_CHAT_MODEL}
      />
    </>
  );
}
