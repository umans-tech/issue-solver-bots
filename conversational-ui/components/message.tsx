'use client';

import cx from 'classnames';
import { AnimatePresence, motion } from 'framer-motion';
import { memo, useMemo, useState, useEffect } from 'react';
import { toast } from 'sonner';

import type { Vote } from '@/lib/db/schema';

import { DocumentToolCall, DocumentToolResult } from './document';
import { Copy, Pencil } from 'lucide-react';
import { Markdown } from './markdown';
import { MessageActions } from './message-actions';
import { PreviewAttachment } from './preview-attachment';
import { Weather } from './weather';
import { WebSearch, WebSearchAnimation, getCombinedWebSearchResults, hasMultipleWebSearchesCalls } from './web-search';
import { FetchWebpage, FetchWebpageAnimation } from './fetch-webpage';
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
import { RemoteCodingAgentAnimation, RemoteCodingStream } from './remote-coding-agent';
import { CodebaseSearchResult, CodebaseSearchPreview } from './codebase-assistant';
import { GitHubMCPAnimation, GitHubMCPResult, isGitHubMCPTool, extractGitHubSources } from './github-mcp';
import { chatModels } from '@/lib/ai/models';
import { TodoDisplay } from './todo-display';
import { ChatMessage, ChatTools } from '@/lib/types';
import { useDataStream } from '@/components/data-stream-provider';
import { ToolUIPart } from 'ai';

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
  regenerate,
  isReadonly,
  requiresScrollPadding,
  selectedChatModel,
}: {
  chatId: string;
  message: ChatMessage;
  vote: Vote | undefined;
  isLoading: boolean;
  setMessages: UseChatHelpers<ChatMessage>['setMessages'];
  regenerate: UseChatHelpers<ChatMessage>['regenerate'];
  isReadonly: boolean;
  requiresScrollPadding: boolean;
  selectedChatModel: string;
}) => {
  const [mode, setMode] = useState<'view' | 'edit'>('view');
  const attachmentsFromMessage = message.parts.filter(
    (part) => part.type === 'file',
  );

  useDataStream();

  // Collect all sources from message parts
  const allSources = useMemo(() => {
    if (!message.parts) return [];
    
    const sources = [];
    
    // Get sources from message parts
    const messageSources = message.parts
      .filter(part => part.type === 'source-url' || part.type === 'source-document')
      .map(part => part.sourceId)
      .filter(source => source !== undefined);
    
    sources.push(...messageSources);
    
    // // Extract GitHub sources from tool invocations
    // const gitHubSources = message.parts
    //   .filter(part => part.type === 'tool-invocation')
    //   .map(part => {
    //     const { toolInvocation } = part;
    //     if (toolInvocation.state === 'result' && isGitHubMCPTool(toolInvocation.toolName)) {
    //       return extractGitHubSources(toolInvocation.toolName, toolInvocation.result, toolInvocation.args);
    //     }
    //     return [];
    //   })
    //   .flat()
    //   .filter(source => source !== undefined);
    
    // sources.push(...gitHubSources);
    
    return sources;
  }, [message.parts]);

  // Combine reasoning parts and associated tool calls in chronological order
  const { combinedReasoningData, nonReasoningParts } = useMemo(() => {
    if (!message.parts) return { combinedReasoningData: { chronologicalItems: [] }, nonReasoningParts: [] };

    // Find indices of reasoning parts
    const reasoningIndices = message.parts
      .map((part, index) => ({ part, index }))
      .filter(({ part }) => part.type === 'reasoning')
      .map(({ index }) => index);
    
    if (reasoningIndices.length === 0) {
      return { combinedReasoningData: { chronologicalItems: [] }, nonReasoningParts: message.parts.map((part, index) => ({ part, index })) };
    }
    
    // Find tool calls that happen during reasoning (between first reasoning and last reasoning + 1)
    const firstReasoningIndex = reasoningIndices[0];
    const lastReasoningIndex = reasoningIndices[reasoningIndices.length - 1];
    
    // Get all parts that belong to reasoning (reasoning parts + tool calls between them)
    const reasoningRelatedParts = message.parts
      .slice(firstReasoningIndex, lastReasoningIndex + 1)
      .map((part, relativeIndex) => ({
        part,
        index: firstReasoningIndex + relativeIndex,
        type: part.type === 'reasoning' ? 'reasoning' as const : part.type.startsWith('tool-') ? 'tool' as const : 'other' as const
      }))
      .filter(({ type }) => type === 'reasoning' || type === 'tool') as Array<{ part: any; index: number; type: 'reasoning' | 'tool' }>;

    // Get non-reasoning parts (excluding tool calls that are part of reasoning)
    const reasoningRelatedIndices = new Set(reasoningRelatedParts.map(({ index }) => index));

    const nonReasoning = message.parts
      .map((part, index) => ({ part, index }))
      .filter(({ index }) => !reasoningRelatedIndices.has(index));
    
    return {
      combinedReasoningData: {
        chronologicalItems: reasoningRelatedParts
      },
      nonReasoningParts: nonReasoning,
    };
  }, [message.parts]);

  // Check if the model supports reasoning (only OpenAI models)
  const modelInfo = chatModels.find(model => model.id === selectedChatModel);
  const supportsReasoning = modelInfo?.provider === 'openai';

  // Check if we should show reasoning placeholder
  const shouldShowReasoningPlaceholder = isLoading && message.role === 'assistant' && supportsReasoning && !message.parts?.some(part => part.type === 'reasoning');
  
  // Detect if reasoning is still streaming
  const hasReasoningParts = message.parts?.some(part => part.type === 'reasoning') || false;
  const hasTextParts = message.parts?.some(part => part.type === 'text') || false;
  
  // Find the last reasoning part and check if there are any text parts after it
  const reasoningIndices = message.parts?.map((part, index) => ({ part, index })).filter(({ part }) => part.type === 'reasoning').map(({ index }) => index) || [];
  const lastReasoningIndex = reasoningIndices.length > 0 ? Math.max(...reasoningIndices) : -1;
  const hasTextAfterReasoning = message.parts?.some((part, index) => part.type === 'text' && index > lastReasoningIndex) || false;

  // Reasoning is considered streaming if:
  // 1. Message is loading AND has reasoning parts AND
  // 2. Either there are no text parts after the last reasoning part
  const reasoningIsStreaming = isLoading && hasReasoningParts && !hasTextAfterReasoning;

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
              'min-h-[65vh]': message.role === 'assistant' && requiresScrollPadding,
            })}
          >
            {attachmentsFromMessage.length > 0 && (
              <div className="flex flex-row justify-end gap-2">
                {attachmentsFromMessage.map((attachment) => (
                  <PreviewAttachment
                    key={attachment.url}
                    attachment={{
                      name: attachment.filename ?? 'file',
                      contentType: attachment.mediaType,
                      url: attachment.url,
                    }}
                  />
                ))}
              </div>
            )}

            {/* Show single combined reasoning component */}
            {(shouldShowReasoningPlaceholder || combinedReasoningData.chronologicalItems.length > 0) && (
              <MessageReasoning
                key={`${message.id}-reasoning-combined`}
                isLoading={shouldShowReasoningPlaceholder}
                chronologicalItems={combinedReasoningData.chronologicalItems}
                isStreaming={shouldShowReasoningPlaceholder || reasoningIsStreaming}
              />
            )}

            {/* Render all non-reasoning parts */}
            {nonReasoningParts.map(({ part, index }) => {
              const key = `message-${message.id}-part-${index}`;
              const { type } = part;

              if (type === 'source-url' || type === 'source-document') {
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
                                <Pencil />
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
                                    toast.error("There's no text to copy!");
                                    return;
                                  }

                                  await navigator.clipboard.writeText(textFromParts);
                                  toast.success('Copied to clipboard!');
                                }}
                              >
                                <Copy />
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
                        regenerate={regenerate}
                      />
                    </div>
                  );
                }
              }

              if (type.startsWith('tool-')) {
                const toolName = type.split('-')[1];
                const { toolCallId, state, input } = part as ToolUIPart<ChatTools>;
                
                if (state === 'input-available') {

                  // Special handling for TodoWrite - render directly without wrapper
                  if (toolName === 'TodoWrite' && (input as any)?.todos) {
                    return (
                      <div key={toolCallId} className="mb-4">
                        <TodoDisplay
                          todos={(input as any).todos}
                          toolName={toolName}
                        />
                      </div>
                    );
                  }

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
                        <DocumentPreview isReadonly={isReadonly} args={input} />
                      ) : toolName === 'updateDocument' ? (
                        <DocumentToolCall
                          type="update"
                          args={input as ChatTools['updateDocument']['input']}
                          isReadonly={isReadonly}
                        />
                      ) : toolName === 'requestSuggestions' ? (
                        <DocumentToolCall
                          type="request-suggestions"
                          args={input as ChatTools['requestSuggestions']['input']}
                          isReadonly={isReadonly}
                        />
                      ) : toolName === 'codebaseSearch' ? (
                        <CodebaseSearchPreview
                          type="codebaseSearch"
                          args={input}
                          isReadonly={isReadonly}
                        />
                      ) : toolName === 'webSearch' ? (
                        <WebSearchAnimation />
                      ) : toolName === 'remoteCodingAgent' ? (
                        <RemoteCodingAgentAnimation />
                      ) : toolName === 'fetchWebpage' ? (
                        <FetchWebpageAnimation url={(input as ChatTools['fetchWebpage']['input'])?.url} />
                      ) : isGitHubMCPTool(toolName) ? (
                        <GitHubMCPAnimation toolName={toolName} args={input} />
                      ) : null}
                    </div>
                  );
                }

                if (state === 'input-streaming') {

                  if (toolName === 'remoteCodingAgent') {
                    const args = input as Partial<ChatTools['remoteCodingAgent']['input']> | undefined;
                    const issueTitle = args?.issue?.title ?? '';
                    const issueDescription = args?.issue?.description ?? '';

                    return (
                      <RemoteCodingStream
                        key={toolCallId}
                        toolCallId={toolCallId}
                        issueTitle={issueTitle}
                        issueDescription={issueDescription}
                        result={null}
                      />
                    );
                  }

                  if (isGitHubMCPTool(toolName)) {
                    const args = input;
                    return (
                      <GitHubMCPAnimation toolName={toolName} args={args} />
                    );
                  }

                  return null;
                }

                if (state === 'output-available') {
                  const toolPart = part as ToolUIPart<ChatTools>;
                  const args = toolPart.input;
                  const result = toolPart.output;

                  // Debug logging for all tool results
                  console.log(`[Tool Result] ${toolName}:`, { result, args, state });

                  // Special handling for TodoWrite - don't show results, already rendered in call state
                  if (toolName === 'TodoWrite') {
                    return null;
                  }

                  // Show single codebase search result normally
                  if (toolName === 'codebaseSearch') {
                    return (
                      <div key={toolCallId}>
                        {result && (
                          <CodebaseSearchResult
                            state={state}
                            result={result}
                            query={(args as ChatTools['codebaseSearch']['input']).query}
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
                          <WebSearch
                            result={result}
                            query={(args as ChatTools['webSearch']['input']).query}
                          />
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
                        <div>
                          <RemoteCodingStream
                            toolCallId={toolCallId}
                            issueTitle={(args as ChatTools['remoteCodingAgent']['input']).issue?.title ?? ''}
                            issueDescription={(args as ChatTools['remoteCodingAgent']['input']).issue?.description ?? ''}
                            isStreaming={false}
                            result={result}
                        />
                        </div>
                      ) : toolName === 'webSearch' ? (
                        <WebSearch
                          result={result}
                          query={(args as ChatTools['webSearch']['input']).query}
                        />
                      ) : toolName === 'codebaseSearch' ? (
                        <CodebaseSearchResult
                          state={state}
                          result={result}
                          query={(args as ChatTools['codebaseSearch']['input']).query}
                        />
                      ) : toolName === 'fetchWebpage' ? (
                        <FetchWebpage
                          result={result}
                          url={(args as ChatTools['fetchWebpage']['input']).url}
                        />
                      ) : isGitHubMCPTool(toolName) ? (
                        <GitHubMCPResult toolName={toolName} result={result} args={args} />
                      ) : (
                        <pre>{JSON.stringify(result, null, 2)}</pre>
                      )}
                    </div>
                  );
                }
              }

              return null;
            })}

            {/* Render all sources consolidated at the end */}
            {!isLoading && allSources.length > 0 && (
              <Sources sources={allSources as any} />
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
    if (prevProps.requiresScrollPadding !== nextProps.requiresScrollPadding) return false;
    if (!equal(prevProps.message.parts, nextProps.message.parts)) return false;
    if (!equal(prevProps.vote, nextProps.vote)) return false;

    return true;
  },
);

export const ThinkingMessage = () => {
  const role = 'assistant';

  return (
    <motion.div
      className="w-full mx-auto max-w-3xl px-4 group/message min-h-[65vh]"
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
