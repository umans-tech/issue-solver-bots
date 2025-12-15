'use client';

import { useState } from 'react';
import { GlobeIcon } from './icons';
import { X } from 'lucide-react';
import { SourceFavicon } from './source-favicon';

// Note: FaviconImage replaced with centralized Favicon component

export interface FetchWebpageResultProps {
  result: string;
  url?: string;
}

export const FetchWebpageAnimation = ({ url }: { url?: string }) => (
  <div className="flex flex-col w-full">
    <div className="text-muted-foreground">
      <span className="animate-pulse">
        Browsing {url ? `${url}...` : 'webpage...'}
      </span>
    </div>
  </div>
);

// Note: Using centralized Favicon component instead of local getFaviconUrl

export function FetchWebpage({ result, url }: FetchWebpageResultProps) {
  const [expanded, setExpanded] = useState(false);

  if (!result || typeof result !== 'string') {
    return null;
  }

  // Extract title from the result string (assuming it starts with # Title)
  const titleMatch = result.match(/^# (.+)/);
  const title = titleMatch ? titleMatch[1] : 'Webpage Content';

  // Extract URL from result if not provided
  const urlMatch = result.match(/\*\*URL:\*\* (.+)/);
  const pageUrl = url || (urlMatch ? urlMatch[1] : '');

  // Extract word count
  const wordCountMatch = result.match(/\*\*Word Count:\*\* (\d+)/);
  const wordCount = wordCountMatch ? wordCountMatch[1] : '0';

  return (
    <div className="mt-1">
      {pageUrl && (
        <div className="flex items-center gap-2 text-sm mb-1">
          <span className="text-muted-foreground">
            <GlobeIcon size={16} />
          </span>
          <span className="text-muted-foreground">Browsed {pageUrl}</span>
        </div>
      )}
      {!expanded ? (
        <div
          className="inline-flex h-8 items-center rounded-full border border-border bg-background px-3 text-sm font-medium gap-1.5 cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => setExpanded(true)}
        >
          <div className="flex items-center gap-1.5">
            {pageUrl && (
              <SourceFavicon url={pageUrl} className="w-4 h-4 rounded-sm" />
            )}
            <span className="text-xs text-muted-foreground">{title}</span>
          </div>
        </div>
      ) : (
        <div className="rounded-md border border-border overflow-hidden bg-background">
          <div
            className="py-1.5 px-3 border-b border-border/50 flex items-center cursor-pointer hover:bg-muted/10 transition-colors"
            onClick={() => setExpanded(false)}
          >
            <div className="flex items-center gap-1.5 flex-grow">
              <span className="text-xs font-medium text-muted-foreground">
                Webpage content
              </span>
            </div>
            <button
              className="text-xs text-muted-foreground hover:text-foreground p-1 rounded hover:bg-muted/50"
              aria-label="Close webpage content"
              onClick={(e) => {
                e.stopPropagation();
                setExpanded(false);
              }}
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="p-3">
            <div className="flex items-start gap-2 mb-3">
              <div className="flex-shrink-0 mt-0.5">
                {pageUrl && (
                  <SourceFavicon url={pageUrl} className="w-5 h-5 rounded-sm" />
                )}
              </div>
              <div className="flex flex-col gap-0">
                <div className="text-base font-medium text-primary">
                  {title}
                </div>
                {pageUrl && (
                  <a
                    href={pageUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-muted-foreground hover:underline truncate"
                  >
                    {pageUrl}
                  </a>
                )}
              </div>
            </div>
            {pageUrl && (
              <div className="mt-3">
                <iframe
                  src={pageUrl}
                  className="w-full h-96 border border-border/50 rounded-md"
                  title={`Preview of ${title}`}
                  sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
                />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
