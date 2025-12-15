'use client';

import { useState } from 'react';
import { GlobeIcon } from './icons';
import { SourceFavicon } from './source-favicon';

interface WebSource {
  title: string;
  url: string;
  content: string;
  publishedDate?: string;
}

export interface WebSearchResultProps {
  result: WebSource[] | any;
  query?: string;
}

export const WebSearchAnimation = () => (
  <div className="flex flex-col w-full">
    <div className="text-muted-foreground">
      <span className="animate-pulse">Searching the web...</span>
    </div>
  </div>
);

export function WebSearch({ result, query }: WebSearchResultProps) {
  const [expanded, setExpanded] = useState(false);

  if (!result || !Array.isArray(result)) {
    return null;
  }

  // Take only the first 3 sources for the collapsed view
  const visibleSources = result.slice(0, 3);

  return (
    <div className="mt-1">
      {query && (
        <div className="flex items-center gap-2 text-sm mb-1">
          <span className="text-muted-foreground">
            <GlobeIcon size={16} />
          </span>
          <span className="text-muted-foreground">
            Searched the web for: "{query}"
          </span>
        </div>
      )}
      {!expanded ? (
        <div
          className="inline-flex h-8 items-center rounded-full border border-border bg-background px-3 text-sm font-medium gap-1.5 cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => setExpanded(true)}
        >
          {visibleSources.map((source, index) => (
            <div key={index} className="flex items-center">
              <SourceFavicon url={source.url} className="w-4 h-4 rounded-sm" />
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-md border border-border overflow-hidden bg-background">
          <div
            className="py-1.5 px-3 border-b border-border/50 flex items-center cursor-pointer hover:bg-muted/10 transition-colors"
            onClick={() => setExpanded(false)}
          >
            <div className="flex items-center gap-1.5 flex-grow">
              <span className="text-xs font-medium text-muted-foreground">
                Search results
              </span>
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
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
          <div className="flex flex-col divide-y divide-border/50">
            {result.map((source: WebSource, index: number) => (
              <div key={index} className="flex flex-col gap-1 p-3">
                <div className="flex items-start gap-2">
                  <div className="flex-shrink-0 mt-0.5">
                    <SourceFavicon
                      url={source.url}
                      className="w-5 h-5 rounded-sm"
                    />
                  </div>
                  <div className="flex flex-col gap-0">
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-base font-medium text-primary hover:underline line-clamp-1"
                    >
                      {source.title || 'Untitled Source'}
                    </a>
                    <div className="text-xs text-muted-foreground truncate">
                      {source.url}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Combine all web search results
export const getCombinedWebSearchResults = (
  message: any,
  isLoading: boolean,
) => {
  if (
    !message.toolInvocations ||
    message.toolInvocations.length === 0 ||
    isLoading
  ) {
    return null;
  }

  // Get all web search results
  const webSearchResults = message.toolInvocations
    .filter(
      (tool: any) =>
        tool.toolName === 'webSearch' &&
        tool.state === 'result' &&
        'result' in tool,
    )
    .map((tool: any) => (tool.state === 'result' ? tool.result : undefined))
    .filter((result: any) => result !== undefined);

  if (webSearchResults.length === 0) {
    return null;
  }

  // Combine all results, ensuring no duplicate URLs
  const urlSet = new Set();
  const combinedResults = [];

  for (const result of webSearchResults) {
    if (!Array.isArray(result)) continue;

    for (const source of result) {
      if (source?.url && !urlSet.has(source.url)) {
        urlSet.add(source.url);
        combinedResults.push(source);
      }
    }
  }

  return combinedResults.length > 0 ? combinedResults : null;
};

export const hasMultipleWebSearchesCalls = (message: any) => {
  if (!message.toolInvocations) return false;
  return (
    message.toolInvocations.filter(
      (tool: any) => tool.toolName === 'webSearch' && tool.state === 'result',
    ).length > 1
  );
};
