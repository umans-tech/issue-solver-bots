'use client';

import { useEffect, useRef } from 'react';
import type { UseChatHelpers } from '@ai-sdk/react';
import type { ChatMessage } from '../lib/types';
import { useDataStream } from '@/components/data-stream-provider';

export interface UseAutoResumeParams {
  autoResume: boolean;
  initialMessages: ChatMessage[];
  resumeStream: UseChatHelpers<ChatMessage>['resumeStream'];
  setMessages: UseChatHelpers<ChatMessage>['setMessages'];
  resumeBlocked?: boolean;
}

export function useAutoResume({
  autoResume,
  initialMessages,
  resumeStream,
  setMessages,
  resumeBlocked = false,
}: UseAutoResumeParams) {
  const { dataStream } = useDataStream();
  const processedCountRef = useRef(0);

  useEffect(() => {
    if (!autoResume) return;
    if (resumeBlocked) return;

    const mostRecentMessage = initialMessages.at(-1);

    if (mostRecentMessage?.role === 'user') {
      resumeStream();
    }

    // we intentionally run this once
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialMessages, resumeBlocked, resumeStream]);

  useEffect(() => {
    if (!autoResume) return;
    if (resumeBlocked) return;
    if (!dataStream) return;

    if (processedCountRef.current > dataStream.length) {
      processedCountRef.current = 0;
    }

    let shouldResume = false;

    for (let index = processedCountRef.current; index < dataStream.length; index += 1) {
      const part = dataStream[index];
      if (part.type !== 'data-appendMessage') continue;

      const message = JSON.parse(part.data);

      setMessages((prev) => {
        const exists = prev.some((existing) => existing.id === message.id);
        if (exists) return prev;
        if (message.role === 'user') {
          shouldResume = true;
        }
        return [...prev, message];
      });
    }

    processedCountRef.current = dataStream.length;

    if (shouldResume) {
      void Promise.resolve(resumeStream()).catch(() => {});
    }
  }, [autoResume, dataStream, resumeBlocked, resumeStream, setMessages]);
}
