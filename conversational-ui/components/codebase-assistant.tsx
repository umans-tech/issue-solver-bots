import { useMemo, useState } from "react";
import { CodeIcon } from "./icons";
import { getFileExtension, getLanguageIcon } from "./sources";
import { Tooltip, TooltipContent, TooltipTrigger } from "./ui/tooltip";

export const CodebaseSearchPreview = ({
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

// Component to display codebase search results
export const CodebaseSearchResult = ({
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
          <div className="flex items-center gap-2 text-sm mb-1">
            <span className="text-muted-foreground">
              <CodeIcon size={16} />
            </span>
            <span className="text-muted-foreground">Searched the codebase for: "{query}"</span>
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
  