import { toast } from 'sonner';
import { useSWRConfig } from 'swr';
import { useCopyToClipboard } from 'usehooks-ts';
import { useRouter } from 'next/navigation';
import { BookOpen, Copy, Split, ThumbsDown, ThumbsUp } from 'lucide-react';

import type { Vote } from '@/lib/db/schema';

import { Button } from './ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from './ui/tooltip';
import { memo, useState } from 'react';
import equal from 'fast-deep-equal';
import type { ChatMessage } from '@/lib/types';
import type { UseChatHelpers } from '@ai-sdk/react';
import { AutoDocPublishDialog } from './auto-doc-publish-dialog';

export function PureMessageActions({
  chatId,
  message,
  vote,
  isLoading,
  isReadonly,
  sendMessage,
}: {
  chatId: string;
  message: ChatMessage;
  vote: Vote | undefined;
  isLoading: boolean;
  isReadonly: boolean;
  sendMessage: UseChatHelpers<ChatMessage>['sendMessage'];
}) {
  const { mutate } = useSWRConfig();
  const [_, copyToClipboard] = useCopyToClipboard();
  const router = useRouter();
  const [isPublishDialogOpen, setIsPublishDialogOpen] = useState(false);

  // Only hide actions when loading
  if (isLoading) return null;

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

  const getMessageText = () =>
    message.parts
      ?.filter((part) => part.type === 'text')
      .map((part) => part.text)
      .join('\n')
      .trim() || '';

  const deriveTitle = (text: string) => {
    const line = text
      .split('\n')
      .map((entry) => entry.trim())
      .find((entry) => entry.length > 0);
    return line ? line.slice(0, 80) : 'Auto Doc';
  };

  const slugify = (value: string) =>
    value
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9\s/-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^\//, '')
      .replace(/\/$/, '') || 'auto-doc';

  const defaultTitle = deriveTitle(getMessageText());
  const defaultPath = slugify(defaultTitle);

  const handlePublish = ({ title, path }: { title: string; path: string }) => {
    const textFromParts = getMessageText();
    if (!textFromParts) {
      toast.error("There's no text to publish yet.");
      return;
    }

    const docTitle = title.trim() || defaultTitle;
    const docPath = path.trim();
    if (!docPath) {
      toast.error('Doc path is required.');
      return;
    }

    const publishPrompt = [
      'Please publish the following assistant response as auto documentation.',
      '',
      `Path: ${docPath}`,
      `Title: ${docTitle}`,
      `Chat ID: ${chatId}`,
      `Message ID: ${message.id}`,
      '',
      'Use the publishAutoDoc tool. The content must be published exactly as provided below.',
      'Infer a concise prompt description from the conversation context.',
      '',
      'CONTENT:',
      '```',
      textFromParts,
      '```',
    ].join('\n');

    sendMessage({
      role: 'user',
      parts: [{ type: 'text', text: publishPrompt }],
    });
  };

  return (
    <TooltipProvider delayDuration={0}>
      <div className="flex flex-row gap-1">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              className="py-1 px-2 h-7 w-7 rounded-full text-muted-foreground opacity-0 group-hover/message:opacity-100 z-10"
              variant="ghost"
              onClick={async () => {
                const textFromParts = message.parts
                  ?.filter((part) => part.type === 'text')
                  .map((part) => part.text)
                  .join('\n')
                  .trim();

                if (!textFromParts) {
                  toast.error("There's no text to copy!");
                  return;
                }

                await copyToClipboard(textFromParts);
                toast.success('Copied to clipboard!');
              }}
            >
              <Copy />
            </Button>
          </TooltipTrigger>
          <TooltipContent sideOffset={5} side="top">
            Copy
          </TooltipContent>
        </Tooltip>

        {message.role === 'assistant' && (
          <>
            {!isReadonly && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    className="py-1 px-2 h-7 w-7 rounded-full text-muted-foreground opacity-0 group-hover/message:opacity-100 z-10"
                    variant="ghost"
                    onClick={() => {
                      const textFromParts = getMessageText();
                      if (!textFromParts) {
                        toast.error("There's no text to publish yet.");
                        return;
                      }
                      setIsPublishDialogOpen(true);
                    }}
                  >
                    <BookOpen />
                  </Button>
                </TooltipTrigger>
                <TooltipContent sideOffset={5} side="top">
                  Publish to Docs
                </TooltipContent>
              </Tooltip>
            )}

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  className="py-1 px-2 h-7 w-7 rounded-full text-muted-foreground opacity-0 group-hover/message:opacity-100 z-10"
                  variant="ghost"
                  onClick={handleBranch}
                >
                  <Split />
                </Button>
              </TooltipTrigger>
              <TooltipContent sideOffset={5} side="top">
                Branch Conversation
              </TooltipContent>
            </Tooltip>

            {!isReadonly && (
              <>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      className="py-1 px-2 h-7 w-7 rounded-full text-muted-foreground opacity-0 group-hover/message:opacity-100 z-10"
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
                      <ThumbsUp />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent sideOffset={5} side="top">
                    Upvote Response
                  </TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      className="py-1 px-2 h-7 w-7 rounded-full text-muted-foreground opacity-0 group-hover/message:opacity-100 z-10"
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
                      <ThumbsDown />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent sideOffset={5} side="top">
                    Downvote Response
                  </TooltipContent>
                </Tooltip>
              </>
            )}
          </>
        )}
      </div>
      <AutoDocPublishDialog
        open={isPublishDialogOpen}
        onOpenChange={setIsPublishDialogOpen}
        defaultTitle={defaultTitle}
        defaultPath={defaultPath}
        onPublish={handlePublish}
      />
    </TooltipProvider>
  );
}

export const MessageActions = memo(
  PureMessageActions,
  (prevProps, nextProps) => {
    if (!equal(prevProps.vote, nextProps.vote)) return false;
    if (prevProps.isLoading !== nextProps.isLoading) return false;
    if (prevProps.isReadonly !== nextProps.isReadonly) return false;

    return true;
  },
);
