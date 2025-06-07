'use client';

import { useState } from 'react';
import { GlobeIcon } from './icons';

// Favicon component with fallback support
const FaviconImage = ({ url, className, alt = "" }: { url: string; className: string; alt?: string }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const fallbackUrls = getFallbackFaviconUrls(url);
  
  if (!fallbackUrls.length) {
    return <GlobeIcon size={16} />;
  }
  
  const handleError = () => {
    if (currentIndex < fallbackUrls.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      // All fallbacks failed, show globe icon
      return;
    }
  };
  
  if (currentIndex >= fallbackUrls.length) {
    return <GlobeIcon size={16} />;
  }
  
  return (
    <img 
      src={fallbackUrls[currentIndex]} 
      alt={alt}
      className={className}
      onError={handleError}
    />
  );
};

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

// Get the site favicon for a URL with multiple fallbacks
const getFaviconUrl = (url: string) => {
  try {
    const domain = new URL(url).hostname;
    // Try multiple favicon services as fallbacks
    return `https://favicon.im/${domain}?larger=true`;
  } catch (e) {
    return undefined;
  }
};

// Fallback favicon URLs
const getFallbackFaviconUrls = (url: string) => {
  try {
    const domain = new URL(url).hostname;
    return [
      `https://favicon.im/${domain}?larger=true`,
      `https://www.google.com/s2/favicons?domain=${domain}&sz=32`,
      `https://${domain}/favicon.ico`,
      `https://icons.duckduckgo.com/ip3/${domain}.ico`
    ];
  } catch (e) {
    return [];
  }
};

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
               <FaviconImage url={pageUrl} className="w-4 h-4 rounded-sm" />
             )}
             <span className="text-xs text-muted-foreground">
               {title}
             </span>
           </div>
        </div>
      ) : (
        <div className="rounded-md border border-border overflow-hidden bg-background">
          <div 
            className="py-1.5 px-3 border-b border-border/50 flex items-center cursor-pointer hover:bg-muted/10 transition-colors"
            onClick={() => setExpanded(false)}
          >
            <div className="flex items-center gap-1.5 flex-grow">
              <span className="text-xs font-medium text-muted-foreground">Webpage content</span>
            </div>
            <button 
              className="text-xs text-muted-foreground hover:text-foreground p-1 rounded hover:bg-muted/50"
              aria-label="Close webpage content"
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
                         <div className="flex items-start gap-2 mb-3">
               <div className="flex-shrink-0 mt-0.5">
                 {pageUrl && (
                   <FaviconImage url={pageUrl} className="w-5 h-5 rounded-sm" />
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