'use client';

import { useState } from 'react';
import { Tooltip, TooltipContent, TooltipTrigger } from './ui/tooltip';
import { CodeXml, X } from 'lucide-react';
import { SourceFavicon } from './source-favicon';
import { GitIcon } from './icons';

// Note: FaviconImage replaced with centralized Favicon component

interface Source {
  id: string;
  url: string;
  title?: string;
  sourceType: 'url';
  providerMetadata?: Record<string, Record<string, any>>;
}

interface SourcesProps {
  sources: Source[];
}

// Note: Using centralized Favicon component instead of local getFaviconUrl

// Check if URL is a web URL (has protocol) vs local file path
const isWebUrl = (url: string): boolean => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

// Get file extension from URL/path
export const getFileExtension = (url: string): string => {
  const filename = url.split('/').pop() || '';
  const lastDot = filename.lastIndexOf('.');
  return lastDot !== -1 ? filename.slice(lastDot + 1).toLowerCase() : '';
};

// Map file extensions to language icon URLs
export const getLanguageIcon = (extension: string): string | null => {
  const iconMap: Record<string, string> = {
    // JavaScript/TypeScript
    js: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/javascript/javascript-original.svg',
    jsx: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/react/react-original.svg',
    ts: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/typescript/typescript-original.svg',
    tsx: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/react/react-original.svg',

    // Python
    py: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg',
    pyx: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg',

    // Java
    java: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/java/java-original.svg',

    // C/C++
    c: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/c/c-original.svg',
    cpp: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/cplusplus/cplusplus-original.svg',
    cc: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/cplusplus/cplusplus-original.svg',
    cxx: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/cplusplus/cplusplus-original.svg',
    h: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/c/c-original.svg',
    hpp: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/cplusplus/cplusplus-original.svg',

    // C#
    cs: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/csharp/csharp-original.svg',

    // Go
    go: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/go/go-original.svg',

    // Rust
    rs: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/rust/rust-plain.svg',

    // PHP
    php: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/php/php-original.svg',

    // Ruby
    rb: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/ruby/ruby-original.svg',

    // Swift
    swift:
      'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/swift/swift-original.svg',

    // Kotlin
    kt: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/kotlin/kotlin-original.svg',
    kts: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/kotlin/kotlin-original.svg',

    // Dart
    dart: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/dart/dart-original.svg',

    // HTML/CSS
    html: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/html5/html5-original.svg',
    htm: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/html5/html5-original.svg',
    css: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/css3/css3-original.svg',
    scss: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/sass/sass-original.svg',
    sass: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/sass/sass-original.svg',
    less: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/less/less-plain-wordmark.svg',

    // Config/Data files
    json: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/json/json-original.svg',
    xml: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/xml/xml-original.svg',
    yaml: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/yaml/yaml-original.svg',
    yml: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/yaml/yaml-original.svg',
    toml: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/toml/toml-original.svg',

    // Shell scripts
    sh: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/bash/bash-original.svg',
    bash: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/bash/bash-original.svg',
    zsh: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/bash/bash-original.svg',
    fish: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/bash/bash-original.svg',

    // Database
    sql: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/mysql/mysql-original.svg',

    // Documentation
    md: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/markdown/markdown-original.svg',
    mdx: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/markdown/markdown-original.svg',

    // Other
    r: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/r/r-original.svg',
    matlab:
      'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/matlab/matlab-original.svg',
    scala:
      'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/scala/scala-original.svg',
    lua: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/lua/lua-original.svg',
    vim: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/vim/vim-original.svg',
    dockerfile:
      'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/docker/docker-original.svg',
  };

  return iconMap[extension] || null;
};

// Determine source type based on URL or provider metadata
const getSourceType = (source: Source): 'web' | 'codebase' | 'github' => {
  // Check if it's a GitHub URL
  if (source.url.includes('github.com')) {
    return 'github';
  }

  // Check provider metadata for hints
  if (source.providerMetadata?.exa) {
    return 'web';
  }

  // Check if it's a web URL
  if (isWebUrl(source.url)) {
    return 'web';
  }

  // Default to codebase for file paths
  return 'codebase';
};

export function Sources({ sources }: SourcesProps) {
  const [expanded, setExpanded] = useState(false);

  if (!sources || sources.length === 0) {
    return null;
  }

  // Deduplicate sources by URL
  const uniqueSources = sources.filter(
    (source, index, arr) =>
      arr.findIndex((s) => s.url === source.url) === index,
  );

  // Separate sources by type
  const webSources = uniqueSources.filter(
    (source) => getSourceType(source) === 'web',
  );
  const codebaseSources = uniqueSources.filter(
    (source) => getSourceType(source) === 'codebase',
  );
  const githubSources = uniqueSources.filter(
    (source) => getSourceType(source) === 'github',
  );

  // Take only the first 3 sources for collapsed view
  const visibleSources = uniqueSources.slice(0, 3);

  return (
    <div className="mt-3">
      {!expanded ? (
        <div
          className="inline-flex h-8 items-center rounded-full border border-border bg-background px-3 text-sm font-medium gap-1.5 cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => setExpanded(true)}
        >
          {visibleSources.map((source, index) => {
            const sourceType = getSourceType(source);
            const extension =
              sourceType === 'codebase' ? getFileExtension(source.url) : '';
            const languageIcon =
              sourceType === 'codebase' ? getLanguageIcon(extension) : null;

            return (
              <div key={source.id} className="flex items-center">
                {sourceType === 'web' ? (
                  <SourceFavicon
                    url={source.url}
                    className="w-4 h-4 rounded-sm"
                  />
                ) : sourceType === 'github' ? (
                  <GitIcon status="none" />
                ) : sourceType === 'codebase' && languageIcon ? (
                  <img
                    src={languageIcon}
                    alt={`${extension} file`}
                    className="w-4 h-4 rounded-sm"
                    onError={(e) => {
                      // Fallback to generic code icon if language icon fails to load
                      const target = e.target as HTMLImageElement;
                      target.style.display = 'none';
                      const fallbackDiv =
                        target.parentElement?.querySelector('.fallback-icon');
                      if (fallbackDiv) {
                        (fallbackDiv as HTMLElement).style.display = 'flex';
                      }
                    }}
                  />
                ) : sourceType === 'codebase' ? (
                  <div className="w-4 h-4 rounded-sm bg-primary/10 flex items-center justify-center fallback-icon">
                    <CodeXml className="w-2.5 h-2.5 text-primary" />
                  </div>
                ) : null}
                {sourceType === 'codebase' && languageIcon && (
                  <div
                    className="w-4 h-4 rounded-sm bg-primary/10 flex items-center justify-center fallback-icon"
                    style={{ display: 'none' }}
                  >
                    <CodeXml className="w-2.5 h-2.5 text-primary" />
                  </div>
                )}
              </div>
            );
          })}
          <span className="text-xs font-medium text-muted-foreground">
            {uniqueSources.length} source{uniqueSources.length !== 1 ? 's' : ''}
          </span>
        </div>
      ) : (
        <div className="rounded-md border border-border overflow-hidden bg-background">
          <div
            className="py-2 px-3 border-b border-border/50 flex items-center cursor-pointer hover:bg-muted/10 transition-colors"
            onClick={() => setExpanded(false)}
          >
            <div className="flex items-center gap-1.5 flex-grow">
              <span className="text-xs font-medium text-muted-foreground">
                {uniqueSources.length} source
                {uniqueSources.length !== 1 ? 's' : ''}
                {(webSources.length > 0 ||
                  codebaseSources.length > 0 ||
                  githubSources.length > 0) &&
                  ` (${[
                    webSources.length > 0 && `${webSources.length} web`,
                    githubSources.length > 0 &&
                      `${githubSources.length} github`,
                    codebaseSources.length > 0 &&
                      `${codebaseSources.length} codebase`,
                  ]
                    .filter(Boolean)
                    .join(', ')})`}
              </span>
            </div>
            <button
              className="text-xs text-muted-foreground hover:text-foreground p-1 rounded hover:bg-muted/50"
              aria-label="Close sources"
              onClick={(e) => {
                e.stopPropagation();
                setExpanded(false);
              }}
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Web Sources Section */}
          {webSources.length > 0 && (
            <div className="flex flex-col divide-y divide-border/50">
              {webSources.length > 1 && (
                <div className="px-3 py-1 bg-muted/20">
                  <span className="text-xs font-medium text-muted-foreground">
                    Web Sources
                  </span>
                </div>
              )}
              {webSources.map((source) => (
                <div key={source.id} className="flex flex-col gap-1 p-3">
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
          )}

          {/* GitHub Sources Section */}
          {githubSources.length > 0 && (
            <div className="flex flex-col divide-y divide-border/50">
              {(githubSources.length > 1 || webSources.length > 0) && (
                <div className="px-3 py-1 bg-muted/20 border-t border-border/50">
                  <span className="text-xs font-medium text-muted-foreground">
                    GitHub Sources
                  </span>
                </div>
              )}
              {githubSources.map((source) => (
                <div key={source.id} className="flex flex-col gap-1 p-3">
                  <div className="flex items-start gap-2">
                    <div className="flex-shrink-0 mt-0.5">
                      <GitIcon status="none" />
                    </div>
                    <div className="flex flex-col gap-0">
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-base font-medium text-primary hover:underline line-clamp-1"
                      >
                        {source.title || 'GitHub Resource'}
                      </a>
                      <div className="text-xs text-muted-foreground truncate">
                        {source.url}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Codebase Sources Section */}
          {codebaseSources.length > 0 && (
            <div className="flex flex-col">
              {(codebaseSources.length > 1 ||
                webSources.length > 0 ||
                githubSources.length > 0) && (
                <div className="px-3 py-1 bg-muted/20 border-t border-border/50">
                  <span className="text-xs font-medium text-muted-foreground">
                    Codebase Sources
                  </span>
                </div>
              )}
              <div className="p-3">
                <div className="flex flex-wrap gap-2">
                  {codebaseSources.map((source) => {
                    const extension = getFileExtension(source.url);
                    const languageIcon = getLanguageIcon(extension);

                    return (
                      <Tooltip key={source.id}>
                        <TooltipTrigger asChild>
                          <div className="inline-flex h-7 items-center justify-center rounded-md border border-primary/10 bg-primary/5 px-3 text-xs font-medium gap-1.5">
                            {languageIcon ? (
                              <div className="relative flex-shrink-0">
                                <img
                                  src={languageIcon}
                                  alt={`${extension} file`}
                                  className="w-3 h-3"
                                  onError={(e) => {
                                    // Fallback to generic code icon if language icon fails to load
                                    const target = e.target as HTMLImageElement;
                                    target.style.display = 'none';
                                    const fallbackDiv =
                                      target.parentElement?.querySelector(
                                        '.fallback-icon',
                                      );
                                    if (fallbackDiv) {
                                      (
                                        fallbackDiv as HTMLElement
                                      ).style.display = 'flex';
                                    }
                                  }}
                                />
                                <div
                                  className="w-3 h-3 flex items-center justify-center fallback-icon absolute top-0 left-0"
                                  style={{ display: 'none' }}
                                >
                                  <CodeXml className="w-2 h-2 text-primary" />
                                </div>
                              </div>
                            ) : (
                              <div className="w-3 h-3 flex items-center justify-center flex-shrink-0">
                                <CodeXml className="w-2 h-2 text-primary" />
                              </div>
                            )}
                            {source.title ||
                              source.url.split('/').pop() ||
                              'Unknown file'}
                          </div>
                        </TooltipTrigger>
                        <TooltipContent side="bottom" className="max-w-[300px]">
                          <span className="text-xs truncate">{source.url}</span>
                        </TooltipContent>
                      </Tooltip>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
