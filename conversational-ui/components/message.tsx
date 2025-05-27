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
  result,
  query
}: {
  state: string;
  result: any;
  query?: string;
}) => {
  const [expanded, setExpanded] = useState(false);

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

  // Take only the first 3 sources for collapsed view
  const visibleSources = uniqueSources.slice(0, 3);

  return (
    <div className="mt-1">
      {query && (
        <div className="flex items-center gap-2 text-sm mb-2">
          <CodeIcon size={16} />
          <span className="text-muted-foreground">Searched the codebase for:</span>
          <SearchIcon size={16} />
          <span className="font-medium">"{query}"</span>
        </div>
      )}
      {!expanded ? (
        <div 
          className="inline-flex h-8 items-center rounded-full border border-border bg-background px-3 text-sm font-medium gap-1.5 cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => setExpanded(true)}
        >
          {visibleSources.map(([_, fileName, filePath], index) => {
            const extension = getFileExtension(filePath);
            const languageIcon = getLanguageIcon(extension);
            
            return (
              <div key={index} className="flex items-center">
                {languageIcon ? (
                  <img 
                    src={languageIcon} 
                    alt={`${extension} file`} 
                    className="w-4 h-4 rounded-sm" 
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                ) : (
                  <div className="w-4 h-4 rounded-sm bg-primary/10 flex items-center justify-center">
                    <svg 
                      width="10" 
                      height="10" 
                      viewBox="0 0 24 24" 
                      fill="none" 
                      xmlns="http://www.w3.org/2000/svg"
                      className="text-primary"
                    >
                      <path 
                        d="M7 8L3 12L7 16M17 8L21 12L17 16M14 4L10 20" 
                        stroke="currentColor" 
                        strokeWidth="2" 
                        strokeLinecap="round" 
                        strokeLinejoin="round"
                      />
                    </svg>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="rounded-md border border-border overflow-hidden bg-background">
          <div 
            className="py-1.5 px-3 border-b border-border/50 flex items-center cursor-pointer hover:bg-muted/10 transition-colors"
            onClick={() => setExpanded(false)}
          >
            <div className="flex items-center gap-1.5 flex-grow">
              <span className="text-xs font-medium text-muted-foreground">Search results</span>
            </div>
            <button 
              className="text-xs text-muted-foreground hover:text-foreground p-1 rounded hover:bg-muted/50"
              aria-label="Close search results"
              onClick={(e) => {
                e.stopPropagation();
                setExpanded(false);
              }}
            >
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                width="14" 
                height="14" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="2" 
                strokeLinecap="round" 
                strokeLinejoin="round"
              >
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
          <div className="p-3">
            <div className="flex flex-wrap gap-2">
              {uniqueSources.map(([_, fileName, filePath], index) => {
                const extension = getFileExtension(filePath);
                const languageIcon = getLanguageIcon(extension);
                
                return (
                  <Tooltip key={index}>
                    <TooltipTrigger asChild>
                      <div className="inline-flex h-7 items-center justify-center rounded-md border border-primary/10 bg-primary/5 px-3 text-xs font-medium gap-1.5">
                        {languageIcon ? (
                          <img 
                            src={languageIcon} 
                            alt={`${extension} file`} 
                            className="w-3 h-3" 
                            onError={(e) => {
                              (e.target as HTMLImageElement).style.display = 'none';
                            }}
                          />
                        ) : (
                          <div className="w-3 h-3 flex items-center justify-center flex-shrink-0">
                            <svg 
                              width="8" 
                              height="8" 
                              viewBox="0 0 24 24" 
                              fill="none" 
                              xmlns="http://www.w3.org/2000/svg"
                              className="text-primary"
                            >
                              <path 
                                d="M7 8L3 12L7 16M17 8L21 12L17 16M14 4L10 20" 
                                stroke="currentColor" 
                                strokeWidth="2" 
                                strokeLinecap="round" 
                                strokeLinejoin="round"
                              />
                            </svg>
                          </div>
                        )}
                        {fileName}
                      </div>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="max-w-[300px]">
                      <span className="text-xs truncate">{filePath}</span>
                    </TooltipContent>
                  </Tooltip>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const CodebaseSearchPreview = ({
  type,
  args,
  isReadonly,
}: {
  type: string;
  args: any;
  isReadonly: boolean;
}) => {
  return <span className="animate-pulse">Searching the codebase...</span>;
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
  message: UIMessage;
  vote: Vote | undefined;
  isLoading: boolean;
  setMessages: UseChatHelpers['setMessages'];
  reload: UseChatHelpers['reload'];
  isReadonly: boolean;
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
                    <div key={key} className="flex flex-row gap-2 items-start">
                      {message.role === 'user' && !isReadonly && (
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              data-testid="message-edit-button"
                              variant="ghost"
                              className="px-2 h-fit rounded-full text-muted-foreground opacity-0 group-hover/message:opacity-100"
                              onClick={() => {
                                setMode('edit');
                              }}
                            >
                              <PencilEditIcon />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>Edit message</TooltipContent>
                        </Tooltip>
                      )}

                      <div
                        data-testid="message-content"
                        className={cn('flex flex-col gap-4', {
                          'bg-primary text-primary-foreground px-3 py-2 rounded-xl':
                            message.role === 'user',
                        })}
                      >
                        <Markdown>{part.text}</Markdown>
                      </div>
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
                      <div key={toolCallId} className="mt-3">
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
                      <div key={toolCallId} className="mt-3">
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

                {!isReadonly && (
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
