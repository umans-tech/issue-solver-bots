import { useState, useEffect } from 'react';
import { useScrollToBottom } from './use-scroll-to-bottom';
import type { UseChatHelpers } from '@ai-sdk/react';
import type { ChatMessage } from '@/lib/types';

export function useMessages({
  chatId,
  status,
}: {
  chatId: string;
  status: UseChatHelpers<ChatMessage>['status'];
}) {
  const {
    containerRef,
    endRef,
    isAtBottom,
    scrollToBottom,
    onViewportEnter,
    onViewportLeave,
  } = useScrollToBottom();

  const [hasSentMessage, setHasSentMessage] = useState(false);

  useEffect(() => {
    if (chatId) {
      scrollToBottom('instant');
      setHasSentMessage(false);
    }
  }, [chatId, scrollToBottom]);

  useEffect(() => {
    if (status === 'submitted') {
      setHasSentMessage(true);
      scrollToBottom();
    }
  }, [status, scrollToBottom]);

  useEffect(() => {
    if (status === 'streaming' && hasSentMessage) {
      scrollToBottom();
    }
  }, [status, hasSentMessage, scrollToBottom]);

  return {
    containerRef,
    endRef,
    isAtBottom,
    scrollToBottom,
    onViewportEnter,
    onViewportLeave,
    hasSentMessage,
  };
}