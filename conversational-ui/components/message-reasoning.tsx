'use client';

import { useState } from 'react';
import { ChevronDownIcon } from './icons';
import { AnimatePresence, motion } from 'framer-motion';
import { Markdown } from './markdown';
import cx from 'classnames';
import { DocumentToolCall, DocumentToolResult } from './document';
import { Weather } from './weather';
import { WebSearch, WebSearchAnimation } from './web-search';
import { FetchWebpage, FetchWebpageAnimation } from './fetch-webpage';
import { DocumentPreview } from './document-preview';
import {
  RemoteCodingAgentAnimation,
  RemoteCodingStream,
} from './remote-coding-agent';
import {
  CodebaseSearchPreview,
  CodebaseSearchResult,
} from './codebase-assistant';
import {
  GitHubMCPAnimation,
  GitHubMCPResult,
  isGitHubMCPTool,
} from './github-mcp';
import {
  isNotionMCPTool,
  NotionMCPAnimation,
  NotionMCPResult,
} from './notion-mcp';

interface MessageReasoningProps {
  isLoading: boolean;
  chronologicalItems?: Array<{
    part: any;
    index: number;
    type: 'reasoning' | 'tool';
  }>;
  isStreaming?: boolean;
}

export function MessageReasoning({
  isLoading,
  chronologicalItems = [],
  isStreaming = false,
}: MessageReasoningProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const hasContent = chronologicalItems.length > 0;

  const variants = {
    collapsed: {
      height: 0,
      opacity: 0,
      marginTop: 0,
      marginBottom: 0,
    },
    expanded: {
      height: 'auto',
      opacity: 1,
      marginTop: '1rem',
      marginBottom: '0.5rem',
    },
  };

  return (
    <div className="flex flex-col">
      {/* Show animated state while streaming, completed state when done */}
      {isStreaming && hasContent ? (
        <div className="flex flex-row gap-2 items-center">
          <span className="animate-pulse text-muted-foreground">
            Reasoning...
          </span>
          <div
            className="cursor-pointer"
            onClick={() => {
              setIsExpanded(!isExpanded);
            }}
          >
            <div
              className={`transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
            >
              <ChevronDownIcon />
            </div>
          </div>
        </div>
      ) : isStreaming && !hasContent ? (
        <div className="flex flex-row gap-2 items-center">
          <span className="animate-pulse text-muted-foreground">
            Reasoning...
          </span>
        </div>
      ) : hasContent ? (
        <div className="flex flex-row gap-2 items-center">
          <div className="text-muted-foreground">Show reasoning</div>
          <div
            className="cursor-pointer"
            onClick={() => {
              setIsExpanded(!isExpanded);
            }}
          >
            <div
              className={`transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
            >
              <ChevronDownIcon />
            </div>
          </div>
        </div>
      ) : null}

      <AnimatePresence initial={false}>
        {isExpanded && hasContent && (
          <motion.div
            key="content"
            initial="collapsed"
            animate="expanded"
            exit="collapsed"
            variants={variants}
            transition={{ duration: 0.2, ease: 'easeInOut' }}
            style={{ overflow: 'hidden' }}
            className="pl-4 text-zinc-600 dark:text-zinc-400 border-l flex flex-col gap-4"
          >
            {/* Render items in chronological order */}
            {chronologicalItems.map((item, itemIndex) => {
              const { part, index, type } = item;

              if (type === 'reasoning') {
                const reasoning = (part as any).text || '';
                return reasoning?.trim() ? (
                  <div key={`reasoning-${index}`}>
                    <Markdown>{reasoning}</Markdown>
                  </div>
                ) : null;
              }

              if (type === 'tool' && part.type === 'tool-invocation') {
                const { toolInvocation } = part;
                const { toolName, toolCallId, state } = toolInvocation;

                if (state === 'call') {
                  const { args } = toolInvocation;

                  return (
                    <div
                      key={toolCallId}
                      className={cx('my-2', {
                        skeleton: ['getWeather'].includes(toolName),
                      })}
                    >
                      {toolName === 'getWeather' ? (
                        <Weather />
                      ) : toolName === 'createDocument' ? (
                        <DocumentPreview isReadonly={true} args={args} />
                      ) : toolName === 'updateDocument' ? (
                        <DocumentToolCall
                          type="update"
                          args={args}
                          isReadonly={true}
                        />
                      ) : toolName === 'requestSuggestions' ? (
                        <DocumentToolCall
                          type="request-suggestions"
                          args={args}
                          isReadonly={true}
                        />
                      ) : toolName === 'codebaseSearch' ? (
                        <CodebaseSearchPreview
                          type="codebaseSearch"
                          args={args}
                          isReadonly={true}
                        />
                      ) : toolName === 'webSearch' ? (
                        <WebSearchAnimation />
                      ) : toolName === 'remoteCodingAgent' ? (
                        <RemoteCodingAgentAnimation />
                      ) : toolName === 'fetchWebpage' ? (
                        <FetchWebpageAnimation url={args?.url} />
                      ) : isNotionMCPTool(toolName) ? (
                        <NotionMCPAnimation toolName={toolName} args={args} />
                      ) : isGitHubMCPTool(toolName) ? (
                        <GitHubMCPAnimation toolName={toolName} args={args} />
                      ) : null}
                    </div>
                  );
                }

                if (state === 'partial-call') {
                  const { args } = toolInvocation;
                  const issueTitle = args?.issue?.title ?? '';
                  const issueDescription = args?.issue?.description ?? '';

                  return toolName === 'remoteCodingAgent' ? (
                    <div key={toolCallId} className="my-2">
                      <RemoteCodingStream
                        toolCallId={toolCallId}
                        issueTitle={issueTitle}
                        issueDescription={issueDescription}
                        result={null}
                      />
                    </div>
                  ) : isNotionMCPTool(toolName) ? (
                    <div key={toolCallId} className="my-2">
                      <NotionMCPAnimation toolName={toolName} args={args} />
                    </div>
                  ) : isGitHubMCPTool(toolName) ? (
                    <div key={toolCallId} className="my-2">
                      <GitHubMCPAnimation toolName={toolName} args={args} />
                    </div>
                  ) : null;
                }

                if (state === 'result') {
                  const { result, args } = toolInvocation;
                  const issueTitle = args?.issue?.title ?? '';
                  const issueDescription = args?.issue?.description ?? '';

                  return (
                    <div key={toolCallId} className="my-2">
                      {toolName === 'getWeather' ? (
                        <Weather weatherAtLocation={result} />
                      ) : toolName === 'createDocument' ? (
                        <DocumentPreview isReadonly={true} result={result} />
                      ) : toolName === 'updateDocument' ? (
                        <DocumentToolResult
                          type="update"
                          result={result}
                          isReadonly={true}
                        />
                      ) : toolName === 'requestSuggestions' ? (
                        <DocumentToolResult
                          type="request-suggestions"
                          result={result}
                          isReadonly={true}
                        />
                      ) : toolName === 'codebaseAssistant' ? (
                        <div />
                      ) : toolName === 'remoteCodingAgent' ? (
                        <RemoteCodingStream
                          toolCallId={toolCallId}
                          issueTitle={issueTitle}
                          issueDescription={issueDescription}
                          isStreaming={false}
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
                      ) : toolName === 'fetchWebpage' ? (
                        <FetchWebpage result={result} url={args?.url} />
                      ) : isNotionMCPTool(toolName) ? (
                        <NotionMCPResult
                          toolName={toolName}
                          result={result}
                          args={args}
                        />
                      ) : isGitHubMCPTool(toolName) ? (
                        <GitHubMCPResult
                          toolName={toolName}
                          result={result}
                          args={args}
                        />
                      ) : (
                        <pre className="text-xs overflow-auto">
                          {JSON.stringify(result, null, 2)}
                        </pre>
                      )}
                    </div>
                  );
                }
              }

              return null;
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
