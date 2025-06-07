'use client';

import type { UIMessage } from 'ai';
import cx from 'classnames';
import { AnimatePresence, motion } from 'framer-motion';
import { memo, useMemo, useState, useEffect } from 'react';

import type { Vote } from '@/lib/db/schema';

import { DocumentToolCall, DocumentToolResult } from './document';
import {
  ChevronDownIcon,
  LoaderIcon,
  PencilEditIcon,
  SparklesIcon,
  RouteIcon,
  SearchIcon,
  CopyIcon,
} from './icons';
import { Markdown } from './markdown';
import { MessageActions } from './message-actions';
import { PreviewAttachment } from './preview-attachment';
import { Weather } from './weather';
import { WebSearch, WebSearchAnimation, getCombinedWebSearchResults, hasMultipleWebSearchesCalls } from './web-search';
import equal from 'fast-deep-equal';
import { cn } from '@/lib/utils';
import { Button } from './ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from './ui/tooltip';
import { MessageEditor } from './message-editor';
import { DocumentPreview } from './document-preview';
import { MessageReasoning } from './message-reasoning';
import { UseChatHelpers } from '@ai-sdk/react';
import Link from 'next/link';
import { Sources, getFileExtension, getLanguageIcon } from './sources';
import { CodeIcon } from './icons';
import { RemoteCodingAgentResult } from './remote-coding-agent';
import { CodebaseSearchResult, CodebaseSearchPreview } from './codebase-assistant';

// Component to display search animation
const SearchingAnimation = () => (
  <div className="flex flex-col w-full">
    <div className="text-muted-foreground">
      <span className="animate-pulse">Searching the codebase...</span>
    </div>
  </div>
);


const PurePreviewMessage = ({
  chatId,
  message,
  vote,
  isLoading,
  setMessages,
  reload,
  isReadonly,
  requiresScrollPadding,
}: {
  chatId: string;
  message: UIMessage;
  vote: Vote | undefined;
  isLoading: boolean;
  setMessages: UseChatHelpers['setMessages'];
  reload: UseChatHelpers['reload'];
  isReadonly: boolean;
  requiresScrollPadding: boolean;
}) => {
  const [mode, setMode] = useState<'view' | 'edit'>('view');

  // Collect all sources from message parts
  const allSources = useMemo(() => {
    if (!message.parts) return [];
    
    return message.parts
      .filter(part => part.type === 'source')
      .map(part => part.source)
      .filter(source => source !== undefined);
  }, [message.parts]);

  return (
    <AnimatePresence>
      <motion.div
        className="w-full mx-auto max-w-3xl px-4 group/message"
        initial={{ y: 5, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        data-role={message.role}
      >
        <div
          className={cn(
            'flex gap-4 w-full group-data-[role=user]/message:ml-auto group-data-[role=user]/message:max-w-2xl',
            {
              'w-full': mode === 'edit',
              'group-data-[role=user]/message:w-fit': mode !== 'edit',
            },
          )}
        >
          <div 
            className={cn("flex flex-col gap-1 w-full relative", {
              'min-h-96': message.role === 'assistant' && requiresScrollPadding,
            })}
          >
            {message.experimental_attachments && (
              <div className="flex flex-row justify-end gap-2">
                {message.experimental_attachments.map((attachment) => (
                  <PreviewAttachment
                    key={attachment.url}
                    attachment={attachment}
                  />
                ))}
              </div>
            )}

            {message.parts?.map((part, index) => {
              const { type } = part;
              const key = `message-${message.id}-part-${index}`;

              if (type === 'reasoning') {
                return (
                  <MessageReasoning
                    key={key}
                    isLoading={isLoading}
                    reasoning={part.reasoning}
                  />
                );
              }

              if (type === 'source') {
                // Skip individual source rendering - we'll show all sources consolidated at the end
                return null;
              }

              if (type === 'text') {
                if (mode === 'view') {
                  return (
                    <div key={key} className="flex flex-col gap-2">
                      <div
                        data-testid="message-content"
                        className={cn('flex flex-col gap-4', {
                          'bg-primary text-primary-foreground px-3 py-2 rounded-xl':
                            message.role === 'user',
                        })}
                      >
                        <Markdown>{part.text}</Markdown>
                      </div>
                      
                      {/* Show edit button below user message */}
                      {message.role === 'user' && !isReadonly && (
                        <div className="flex justify-end gap-1">
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                data-testid="message-edit-button"
                                variant="ghost"
                                className="py-1 px-2 h-7 w-7 rounded-full text-muted-foreground opacity-0 group-hover/message:opacity-100"
                                onClick={() => {
                                  setMode('edit');
                                }}
                              >
                                <PencilEditIcon />
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>Edit message</TooltipContent>
                          </Tooltip>
                          
                          {/* Copy button for user messages */}
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                className="py-1 px-2 h-7 w-7 rounded-full text-muted-foreground opacity-0 group-hover/message:opacity-100"
                                variant="ghost"
                                onClick={async () => {
                                  const textFromParts = message.parts
                                    ?.filter((part) => part.type === 'text')
                                    .map((part) => part.text)
                                    .join('\n')
                                    .trim();

                                  if (!textFromParts) {
                                    return;
                                  }

                                  await navigator.clipboard.writeText(textFromParts);
                                }}
                              >
                                <CopyIcon />
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>Copy</TooltipContent>
                          </Tooltip>
                        </div>
                      )}
                    </div>
                  );
                }

                if (mode === 'edit') {
                  return (
                    <div key={key} className="flex flex-row gap-2 items-start">
                      <div className="size-8" />

                      <MessageEditor
                        key={message.id}
                        message={message}
                        setMode={setMode}
                        setMessages={setMessages}
                        reload={reload}
                      />
                    </div>
                  );
                }
              }

              if (type === 'tool-invocation') {
                const { toolInvocation } = part;
                const { toolName, toolCallId, state } = toolInvocation;
                
                if (state === 'call') {
                  const { args } = toolInvocation;

                  return (
                    <div
                      key={toolCallId}
                      className={cx({
                        skeleton: ['getWeather'].includes(toolName),
                      })}
                    >
                      {toolName === 'getWeather' ? (
                        <Weather />
                      ) : toolName === 'createDocument' ? (
                        <DocumentPreview isReadonly={isReadonly} args={args} />
                      ) : toolName === 'updateDocument' ? (
                        <DocumentToolCall
                          type="update"
                          args={args}
                          isReadonly={isReadonly}
                        />
                      ) : toolName === 'requestSuggestions' ? (
                        <DocumentToolCall
                          type="request-suggestions"
                          args={args}
                          isReadonly={isReadonly}
                        />
                      ) : toolName === 'codebaseSearch' ? (
                        <CodebaseSearchPreview
                          type="codebaseSearch"
                          args={args}
                          isReadonly={isReadonly}
                        />
                      ) : toolName === 'webSearch' ? (
                        <WebSearchAnimation />
                      ) : null}
                    </div>
                  );
                }

                if (state === 'result') {
                  const { result, args } = toolInvocation;

                  // Show single codebase search result normally
                  if (toolName === 'codebaseSearch') {
                    return (
                      <div key={toolCallId}>
                        {result && (
                          <CodebaseSearchResult
                            state={state}
                            result={result}
                            query={args?.query}
                          />
                        )}
                      </div>
                    );
                  }

                  // Show web search results
                  if (toolName === 'webSearch') {

                    return (
                      <div key={toolCallId}>
                        {result && (
                          <WebSearch result={result} query={args?.query} />
                        )}
                      </div>
                    );
                  }

                  return (
                    <div key={toolCallId}>
                      {toolName === 'getWeather' ? (
                        <Weather weatherAtLocation={result} />
                      ) : toolName === 'createDocument' ? (
                        <DocumentPreview
                          isReadonly={isReadonly}
                          result={result}
                        />
                      ) : toolName === 'updateDocument' ? (
                        <DocumentToolResult
                          type="update"
                          result={result}
                          isReadonly={isReadonly}
                        />
                      ) : toolName === 'requestSuggestions' ? (
                        <DocumentToolResult
                          type="request-suggestions"
                          result={result}
                          isReadonly={isReadonly}
                        />
                      ) : toolName === 'codebaseAssistant' ? (
                          <div>
                          </div>
                      ) : toolName === 'remoteCodingAgent' ? (
                          <RemoteCodingAgentResult
                            state={state}
                            result={result}
                          />
                      ) : toolName === 'webSearch' ? (
                        <WebSearch result={result} query={args?.query} />
                      ) : toolName === 'codebaseSearch' ? (
                        <CodebaseSearchResult
                          state={state}
                          result={result}
                          query={args?.query}
                        />
                      ) : (
                        <pre>{JSON.stringify(result, null, 2)}</pre>
                      )}
                    </div>
                  );
                }
              }
            })}

            {/* Render all sources consolidated at the end */}
            {!isLoading && allSources.length > 0 && (
              <Sources sources={allSources} />
            )}

                {!isReadonly && message.role === 'assistant' && (
                    <MessageActions
                      key={`action-${message.id}-tools`}
                      chatId={chatId}
                      message={message}
                      vote={vote}
                      isLoading={isLoading}
                      isReadonly={isReadonly}
                    />
                )}
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export const PreviewMessage = memo(
  PurePreviewMessage,
  (prevProps, nextProps) => {
    if (prevProps.isLoading !== nextProps.isLoading) return false;
    if (prevProps.message.id !== nextProps.message.id) return false;
    if (!equal(prevProps.message.parts, nextProps.message.parts)) return false;
    if (!equal(prevProps.vote, nextProps.vote)) return false;

    return true;
  },
);

export const ThinkingMessage = () => {
  const role = 'assistant';

  return (
    <motion.div
      className="w-full mx-auto max-w-3xl px-4 group/message "
      initial={{ y: 5, opacity: 0 }}
      animate={{ y: 0, opacity: 1, transition: { delay: 1 } }}
      data-role={role}
    >
      <div
        className={cx(
          'flex gap-4 group-data-[role=user]/message:px-3 w-full group-data-[role=user]/message:w-fit group-data-[role=user]/message:ml-auto group-data-[role=user]/message:max-w-2xl group-data-[role=user]/message:py-2 rounded-xl',
          {
            'group-data-[role=user]/message:bg-muted': true,
          },
        )}
      >
        <div className="flex flex-col gap-2 w-full">
          <div className="flex flex-col gap-4 text-muted-foreground">
            <span className="animate-pulse">Thinking...</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
