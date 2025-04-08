import type { Message } from 'ai';
import { toast } from 'sonner';
import { useSWRConfig } from 'swr';
import { useCopyToClipboard } from 'usehooks-ts';
import { useRouter } from 'next/navigation';

import type { Vote } from '@/lib/db/schema';

import { CopyIcon, ThumbDownIcon, ThumbUpIcon, BranchIcon } from './icons';
import { Button } from './ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from './ui/tooltip';
import { memo } from 'react';
import equal from 'fast-deep-equal';

export function PureMessageActions({
  chatId,
  message,
  vote,
  isLoading,
}: {
  chatId: string;
  message: Message;
  vote: Vote | undefined;
  isLoading: boolean;
}) {
  const { mutate } = useSWRConfig();
  const [_, copyToClipboard] = useCopyToClipboard();
  const router = useRouter();

  // Only hide actions when loading or when there are tool invocations
  if (isLoading) return null;
  
  // Check if message has tool invocations, but don't return null if it does
  const hasToolInvocations = message.toolInvocations && message.toolInvocations.length > 0;

  const handleBranch = async () => {
    try {
      const response = await fetch('/api/branch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sourceChatId: chatId,
          messageId: message.id,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to branch conversation');
      }

      const data = await response.json();
      
      if (data.success && data.newChatId) {
        toast.success('Created new branch!');
        // Navigate to the new chat
        router.push(`/chat/${data.newChatId}`);
      } else {
        throw new Error('Failed to branch conversation');
      }
    } catch (error) {
      console.error('Error branching conversation:', error);
      toast.error('Failed to branch conversation');
    }
  };

  return (
    <TooltipProvider delayDuration={0}>
      <div className="flex flex-col gap-1">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              className="py-1 px-2 h-fit rounded-full text-muted-foreground opacity-0 group-hover/message:opacity-100 z-10"
              variant="ghost"
              onClick={async () => {
                await copyToClipboard(message.content as string);
                toast.success('Copied to clipboard!');
              }}
            >
              <CopyIcon />
            </Button>
          </TooltipTrigger>
          <TooltipContent sideOffset={5} side="right">Copy</TooltipContent>
        </Tooltip>

        {message.role === 'assistant' && !hasToolInvocations && (
          <>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  className="py-1 px-2 h-fit rounded-full text-muted-foreground opacity-0 group-hover/message:opacity-100 z-10"
                  variant="ghost"
                  onClick={handleBranch}
                >
                  <BranchIcon />
                </Button>
              </TooltipTrigger>
              <TooltipContent sideOffset={5} side="right">Branch Conversation</TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  className="py-1 px-2 h-fit rounded-full text-muted-foreground opacity-0 group-hover/message:opacity-100 z-10"
                  disabled={vote?.isUpvoted}
                  variant="ghost"
                  onClick={async () => {
                    const upvote = fetch('/api/vote', {
                      method: 'PATCH',
                      body: JSON.stringify({
                        chatId,
                        messageId: message.id,
                        type: 'up',
                      }),
                    });

                    toast.promise(upvote, {
                      loading: 'Upvoting Response...',
                      success: () => {
                        mutate<Array<Vote>>(
                          `/api/vote?chatId=${chatId}`,
                          (currentVotes) => {
                            if (!currentVotes) return [];

                            const votesWithoutCurrent = currentVotes.filter(
                              (vote) => vote.messageId !== message.id,
                            );

                            return [
                              ...votesWithoutCurrent,
                              {
                                chatId,
                                messageId: message.id,
                                isUpvoted: true,
                              },
                            ];
                          },
                          { revalidate: false },
                        );

                        return 'Upvoted Response!';
                      },
                      error: 'Failed to upvote response.',
                    });
                  }}
                >
                  <ThumbUpIcon />
                </Button>
              </TooltipTrigger>
              <TooltipContent sideOffset={5} side="right">Upvote Response</TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  className="py-1 px-2 h-fit rounded-full text-muted-foreground opacity-0 group-hover/message:opacity-100 z-10"
                  variant="ghost"
                  disabled={vote && !vote.isUpvoted}
                  onClick={async () => {
                    const downvote = fetch('/api/vote', {
                      method: 'PATCH',
                      body: JSON.stringify({
                        chatId,
                        messageId: message.id,
                        type: 'down',
                      }),
                    });

                    toast.promise(downvote, {
                      loading: 'Downvoting Response...',
                      success: () => {
                        mutate<Array<Vote>>(
                          `/api/vote?chatId=${chatId}`,
                          (currentVotes) => {
                            if (!currentVotes) return [];

                            const votesWithoutCurrent = currentVotes.filter(
                              (vote) => vote.messageId !== message.id,
                            );

                            return [
                              ...votesWithoutCurrent,
                              {
                                chatId,
                                messageId: message.id,
                                isUpvoted: false,
                              },
                            ];
                          },
                          { revalidate: false },
                        );

                        return 'Downvoted Response!';
                      },
                      error: 'Failed to downvote response.',
                    });
                  }}
                >
                  <ThumbDownIcon />
                </Button>
              </TooltipTrigger>
              <TooltipContent sideOffset={5} side="right">Downvote Response</TooltipContent>
            </Tooltip>
          </>
        )}
      </div>
    </TooltipProvider>
  );
}

export const MessageActions = memo(
  PureMessageActions,
  (prevProps, nextProps) => {
    if (!equal(prevProps.vote, nextProps.vote)) return false;
    if (prevProps.isLoading !== nextProps.isLoading) return false;

    return true;
  },
);
