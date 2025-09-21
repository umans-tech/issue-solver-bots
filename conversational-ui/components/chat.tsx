'use client';

import { DefaultChatTransport } from 'ai';
import pRetry from 'p-retry';
import { useChat } from '@ai-sdk/react';
import { useState, useEffect, useCallback } from 'react';
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
  const [resumeBlocked, setResumeBlocked] = useState(false);

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
        // Read the freshest model selection directly at call time (handles quick switch before submit)
        const currentModelId = (() => {
          try {
            const raw = localStorage.getItem('chat-model');
            console.log('raw', raw);
            const parsed = raw ? JSON.parse(raw) : null;
            return parsed || storedModelId || DEFAULT_CHAT_MODEL;
          } catch {
            return storedModelId || DEFAULT_CHAT_MODEL;
          }
        })();
        return {
          body: {
            ...body,
            id,
            messages,
            knowledgeBaseId: knowledgeBaseIdState,
            // Ensure the freshest model always wins (even on regenerate)
            selectedChatModel: currentModelId,
          },
        };
      },
    }),
    onData: (dataPart) => {
      setDataStream((ds) => (ds ? [...ds, dataPart] : [dataPart]));
    },
    onFinish: () => {
      mutate('/api/history');
    },
    onError: (error) => {
      console.error('Error in useChat:\n', error.message);
      console.error('Call stack:\n', error.stack);
      if (resumeBlocked) {
        return;
      }
      if (isNetworkLikeError(error)) {
        void pRetry(() => Promise.resolve(resumeStream()), {
          retries: 3,
          factor: 2,
          minTimeout: 800,
          maxTimeout: 3000,
          randomize: true,
        }).catch(() => {});
        return;
      }
      toast.error('An error occured, please try again!');
    },
  });

  const handleStop = useCallback(() => {
    setResumeBlocked(true);
    setMessages((prev) => {
      const next = [...prev];
      for (let i = next.length - 1; i >= 0; i -= 1) {
        if (next[i].role === 'assistant') {
          next[i] = {
            ...next[i],
            parts: next[i].parts.filter((part) => part.type !== 'reasoning'),
          };
          break;
        }
      }
      return next;
    });
    return stop();
  }, [setMessages, stop]);

  const handleSendMessage = useCallback(
    (...args: Parameters<typeof sendMessage>) => {
      setResumeBlocked(false);
      return sendMessage(...args);
    },
    [sendMessage],
  );

  const handleRegenerate = useCallback(
    (...args: Parameters<typeof regenerate>) => {
      setResumeBlocked(false);
      return regenerate(...args);
    },
    [regenerate],
  );

  // Optional: auto-resume when network is back or tab becomes visible
  useEffect(() => {
    if (!autoResume) return;
    if (resumeBlocked) return;

    const onOnline = () => { void Promise.resolve(resumeStream()).catch(() => {}); };
    const onVisible = () => {
      if (document.visibilityState === 'visible') {
        void Promise.resolve(resumeStream()).catch(() => {});
      }
    };
    window.addEventListener('online', onOnline);
    document.addEventListener('visibilitychange', onVisible);
    return () => {
      window.removeEventListener('online', onOnline);
      document.removeEventListener('visibilitychange', onVisible);
    };
  }, [autoResume, resumeBlocked, resumeStream]);



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
    resumeBlocked,
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
          regenerate={handleRegenerate}
          stop={handleStop}
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
              stop={handleStop}
              attachments={attachments}
              setAttachments={setAttachments}
              messages={messages}
              setMessages={setMessages}
              sendMessage={handleSendMessage}
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
        stop={handleStop}
        attachments={attachments}
        setAttachments={setAttachments}
        sendMessage={handleSendMessage}
        messages={messages}
        setMessages={setMessages}
        regenerate={handleRegenerate}
        votes={votes}
        isReadonly={isReadonly}
        selectedModelId={storedModelId || DEFAULT_CHAT_MODEL}
      />
    </>
  );
}
