'use client';

import type { ChatRequestOptions, Message } from 'ai';
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
import Link from 'next/link';

// Component to display search animation
const SearchingAnimation = () => (
  <div className="flex flex-col w-full">
    <div className="text-muted-foreground">
      <span className="animate-pulse">Searching the codebase...</span>
    </div>
  </div>
);

const RemoteCodingAgentResult = ({
  state,
  result
}: {
  state: string;
  result: any;
}) => {
  return (
    <div className="bg-background border py-2 px-3 rounded-xl w-fit flex flex-row gap-3 items-center">
      <div className="text-muted-foreground">
        <RouteIcon size={16} />
      </div>
      <Link 
        href={`/tasks/${result.processId}`} 
        className="text-primary hover:text-primary/80 flex items-center gap-2 transition-colors"
      >
        <span>View remote task progress</span>
        <svg 
          width="14" 
          height="14" 
          viewBox="0 0 24 24" 
          fill="none" 
          xmlns="http://www.w3.org/2000/svg"
          className="text-primary"
        >
          <path 
            d="M7 17L17 7M17 7H8M17 7V16" 
            stroke="currentColor" 
            strokeWidth="2" 
            strokeLinecap="round" 
            strokeLinejoin="round"
          />
        </svg>
      </Link>
    </div>
  );
};

// Component to display codebase search results
const CodebaseSearchResult = ({
  state,
  result
}: {
  state: string;
  result: any;
}) => {
  const [showAll, setShowAll] = useState(false);

  // Parse source files from the result
  const sources = useMemo(() => {
    if (Array.isArray(result)) {
      return result; // Already processed array
    }

    if (typeof result !== 'string') {
      return [];
    }

    // Parse XML result
    return Array.from(result.matchAll(/<result file_name='([^']+)' file_path='([^']+)'>/g));
  }, [result]);

  // Filter for unique sources based on file_path
  const uniqueSources = useMemo(() => {
    const uniquePaths = new Set();
    return sources.filter(([_, fileName, filePath]) => {
      if (!filePath || uniquePaths.has(filePath)) {
        return false;
      }
      uniquePaths.add(filePath);
      return true;
    });
  }, [sources]);

  // If no unique sources, don't render anything
  if (uniqueSources.length === 0) {
    return null;
  }

  const displayCount = showAll ? uniqueSources.length : Math.min(3, uniqueSources.length);

  return (
    <div className="rounded-md border border-border p-3 bg-muted/30">
      <div className="text-xs font-medium text-muted-foreground mb-2">Sources from codebase:</div>
      <div className="flex flex-wrap gap-2">
        {uniqueSources.slice(0, displayCount).map(([_, fileName, filePath], index) => (
          <Tooltip key={index}>
            <TooltipTrigger asChild>
              <div
                className="inline-flex h-7 items-center justify-center rounded-md border border-primary/10 bg-primary/5 px-3 text-xs font-medium"
              >
                {fileName}
              </div>
            </TooltipTrigger>
            <TooltipContent side="bottom" className="max-w-[300px]">
              <span className="text-xs truncate">{filePath}</span>
            </TooltipContent>
          </Tooltip>
        ))}

        {uniqueSources.length > 3 && (
          <Button
            variant="ghost"
            size="sm"
            className="h-7 text-xs text-primary"
            onClick={() => setShowAll(!showAll)}
          >
            {showAll ? 'Show less' : `+${uniqueSources.length - 3} more`}
          </Button>
        )}
      </div>
    </div>
  );
};

const PurePreviewMessage = ({
  chatId,
  message,
  vote,
  isLoading,
  setMessages,
  reload,
  isReadonly,
}: {
  chatId: string;
  message: Message;
  vote: Vote | undefined;
  isLoading: boolean;
  setMessages: (
    messages: Message[] | ((messages: Message[]) => Message[]),
  ) => void;
  reload: (
    chatRequestOptions?: ChatRequestOptions,
  ) => Promise<string | null | undefined>;
  isReadonly: boolean;
}) => {
  const [mode, setMode] = useState<'view' | 'edit'>('view');

  // Debug message rendering - helpful for troubleshooting UI issues
  useEffect(() => {
    console.log(`Rendering message ${message.id}:`, {
      role: message.role,
      hasContent: !!message.content,
      hasToolInvocations: !!(message.toolInvocations && message.toolInvocations.length > 0),
      toolCount: message.toolInvocations?.length || 0,
      isLoading
    });
  }, [message, isLoading]);

  // Combine all codebase search results
  const combinedCodebaseSearchResults = useMemo(() => {
    if (!message.toolInvocations || message.toolInvocations.length === 0 || isLoading) {
      return null;
    }

    // Get all codebase search results
    const codebaseSearchResults = message.toolInvocations
      .filter(tool =>
        tool.toolName === 'codebaseSearch' &&
        tool.state === 'result' &&
        'result' in tool
      )
      .map(tool => tool.state === 'result' ? tool.result : undefined)
      .filter(result => result !== undefined);

    if (codebaseSearchResults.length === 0) {
      return null;
    }

    // Collect all source matches from all results
    const allMatches = [];

    for (const result of codebaseSearchResults) {
      if (typeof result !== 'string') continue;

      const matches = Array.from(
        result.matchAll(/<result file_name='([^']+)' file_path='([^']+)'>/g)
      );

      allMatches.push(...matches);
    }

    return allMatches.length > 0 ? allMatches : null;
  }, [message.toolInvocations, isLoading]);

  // Combine all web search results
  const combinedWebSearchResults = getCombinedWebSearchResults(message, isLoading);

  // Check if we should render codebase search results separately or combined
  const hasMultipleCodebaseSearches = useMemo(() => {
    if (!message.toolInvocations) return false;
    return message.toolInvocations.filter(
      tool => tool.toolName === 'codebaseSearch' && tool.state === 'result'
    ).length > 1;
  }, [message.toolInvocations]);

  // Check if we should render web search results separately or combined
  const hasMultipleWebSearches = hasMultipleWebSearchesCalls(message);

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
          <div className="flex flex-col gap-4 w-full relative">
            {/* Remove the assistant action buttons from left position */}

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

            {message.reasoning && (
              <MessageReasoning
                isLoading={isLoading}
                reasoning={message.reasoning}
              />
            )}

            {(message.content || message.reasoning) && mode === 'view' && (
              <div className="flex flex-col gap-2 items-start w-full">
                <div
                  className={cn('flex flex-col gap-4 overflow-hidden w-full', {
                    'bg-primary text-primary-foreground px-3 py-2 rounded-lg':
                      message.role === 'user',
                  })}
                >
                  <Markdown>{message.content as string}</Markdown>
                </div>

                <div className="flex flex-row gap-1 mt-1 ml-auto">
                  {message.role === 'user' && !isReadonly && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="ghost"
                          className="py-1 px-2 h-7 w-7 rounded-full text-muted-foreground opacity-0 group-hover/message:opacity-100"
                          onClick={() => {
                            setMode('edit');
                          }}
                        >
                          <PencilEditIcon />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent sideOffset={5}>Edit message</TooltipContent>
                    </Tooltip>
                  )}
                  <MessageActions
                    key={`action-${message.id}-user`}
                    chatId={chatId}
                    message={message}
                    vote={vote}
                    isLoading={isLoading}
                    isReadonly={isReadonly}
                  />
                </div>
              </div>
            )}

            {message.content && mode === 'edit' && (
              <div className="flex flex-row gap-2 items-start">
                <div className="size-8" />

                <MessageEditor
                  key={message.id}
                  message={message}
                  setMode={setMode}
                  setMessages={setMessages}
                  reload={reload}
                />
              </div>
            )}

            {message.toolInvocations && message.toolInvocations.length > 0 && (
              <div className="flex flex-col gap-4">
                <div className={cn('flex flex-col gap-4 overflow-hidden w-full')}>
                  {message.toolInvocations.map((toolInvocation) => {
                    const { toolName, toolCallId, state, args } = toolInvocation;
                    // For TypeScript: explicitly access result via toolInvocation.result
                    const result = 'result' in toolInvocation ? toolInvocation.result : undefined;

                    // Handle codebase search animation separately
                    if (toolName === 'codebaseSearch' && state === 'call') {
                      return (
                        <div className="text-muted-foreground" key={toolCallId}>
                          <span className="animate-pulse">Searching the codebase...</span>
                        </div>
                      );
                    }

                    // Handle web search animation separately
                    if (toolName === 'webSearch' && state === 'call') {
                      return <WebSearchAnimation key={toolCallId} />;
                    }

                    if (state === 'result') {
                      // Skip individual codebase search results if we have multiple searches
                      if (toolName === 'codebaseSearch' && hasMultipleCodebaseSearches) {
                        return null;
                      }

                      // Show single codebase search result normally
                      if (toolName === 'codebaseSearch' && !hasMultipleCodebaseSearches) {
                        return (
                          <div key={toolCallId} className="mt-3">
                            {!isLoading && result && (
                              <CodebaseSearchResult
                                state={state}
                                result={result}
                              />
                            )}
                          </div>
                        );
                      }

                      // Show web search results
                      if (toolName === 'webSearch') {
                        // Skip individual web search results if we have multiple searches
                        if (hasMultipleWebSearches) {
                          return null;
                        }

                        return (
                          <div key={toolCallId} className="mt-3">
                            {!isLoading && result && (
                              <WebSearch result={result} />
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
                          ) : (
                            <pre>{JSON.stringify(result, null, 2)}</pre>
                          )}
                        </div>
                      );
                    }
          

                    // For states other than 'result' or 'running' during codebaseSearch
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
                          // For codebaseSearch in other states, don't show anything
                          null
                        ) : toolName === 'webSearch' ? (
                          // For webSearch in other states, show the animation
                          <WebSearchAnimation />
                        ) : null}
                      </div>
                    );
                  })}

                  {/* Display combined codebase search results at the end ONLY if we have multiple searches */}
                  {combinedCodebaseSearchResults && hasMultipleCodebaseSearches && !isLoading && (
                    <div className="mt-3">
                      <CodebaseSearchResult
                        state="result"
                        result={combinedCodebaseSearchResults}
                      />
                    </div>
                  )}

                  {/* Display combined web search results at the end ONLY if we have multiple searches */}
                  {combinedWebSearchResults && hasMultipleWebSearches && !isLoading && (
                    <div className="mt-3">
                      <WebSearch result={combinedWebSearchResults} />
                    </div>
                  )}
                </div>

                {/* Only show actions here if there's no message content (to avoid duplication) */}
                {message.role === 'assistant' && !message.content && (
                  <div className="flex flex-row gap-1 mt-1 ml-auto">
                    <MessageActions
                      key={`action-${message.id}-tools`}
                      chatId={chatId}
                      message={message}
                      vote={vote}
                      isLoading={isLoading}
                      isReadonly={isReadonly}
                    />
                  </div>
                )}
              </div>
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
    if (prevProps.message.reasoning !== nextProps.message.reasoning)
      return false;
    if (prevProps.message.content !== nextProps.message.content) return false;
    if (
      !equal(
        prevProps.message.toolInvocations,
        nextProps.message.toolInvocations,
      )
    )
      return false;
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
