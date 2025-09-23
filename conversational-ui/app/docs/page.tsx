"use client";

import { useCallback, useEffect, useRef, useState } from 'react';
import { SharedHeader } from '@/components/shared-header';
import { Markdown } from '@/components/markdown';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { SearchIcon, CopyIcon } from '@/components/icons';
import { useSession } from 'next-auth/react';

export default function DocsPage() {
  const { data: session } = useSession();
  const kbId = session?.user?.selectedSpace?.knowledgeBaseId;
  // commit sha is not currently typed on selectedSpace; leave undefined and rely on versions API
  const currentCommit = undefined as string | undefined;

  const [commitSha, setCommitSha] = useState<string | undefined>(currentCommit);
  const [versions, setVersions] = useState<string[]>([]);
  const [, setIndexMd] = useState<string>('');
  const [fileList, setFileList] = useState<string[]>([]);
  const [titleMap, setTitleMap] = useState<Record<string, string>>({});
  const [activePath, setActivePath] = useState<string | null>(null);
  const [content, setContent] = useState<string>('');
  const [q, setQ] = useState('');
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<{ path: string; snippet: string; line?: number }[]>([]);
  const [selectedIdx, setSelectedIdx] = useState<number>(0);
  const contentRef = useRef<HTMLDivElement | null>(null);
  const [toc, setToc] = useState<{ id: string; text: string; level: number }[]>([]);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const searchInputRef = useRef<HTMLInputElement | null>(null);
  const highlightTermRef = useRef<string | null>(null);

  // Load versions on mount
  useEffect(() => {
    if (!kbId) return;
    (async () => {
      try {
        const res = await fetch(`/api/docs/versions?kbId=${encodeURIComponent(kbId)}`, { cache: 'no-store' });
        const data = await res.json();
        if (Array.isArray(data.versions)) {
          setVersions(data.versions);
          if (!commitSha && data.versions.length > 0) {
            setCommitSha(data.versions[data.versions.length - 1]);
          }
        }
      } catch {}
    })();
  }, [kbId]);

  // Load index.md and files list
  useEffect(() => {
    if (!kbId || !commitSha) return;
    (async () => {
      try {
        const idx = await fetch(`/api/docs/index?kbId=${encodeURIComponent(kbId)}&commitSha=${encodeURIComponent(commitSha)}`, { cache: 'no-store' });
        const idxJson = await idx.json();
        setIndexMd(idxJson?.content || '');
      } catch {
        setIndexMd('');
      }
      try {
        const r = await fetch(`/api/docs/list?kbId=${encodeURIComponent(kbId)}&commitSha=${encodeURIComponent(commitSha)}`, { cache: 'no-store' });
        const j = await r.json();
        const files = Array.isArray(j.files) ? j.files : [];
        setFileList(files);
        // lazily resolve titles for index entries
        const entries = await Promise.all(files.map(async (f: string) => {
          try {
            const tr = await fetch(`/api/docs/title?kbId=${encodeURIComponent(kbId)}&commitSha=${encodeURIComponent(commitSha)}&path=${encodeURIComponent(f)}`, { cache: 'no-store' });
            const tj = await tr.json();
            return [f, tj?.title || f] as const;
          } catch {
            return [f, f] as const;
          }
        }));
        const map: Record<string, string> = {};
        for (const [k, v] of entries) map[k] = v;
        setTitleMap(map);
      } catch {
        setFileList([]);
      }
    })();
  }, [kbId, commitSha]);

  useEffect(() => {
    if (!kbId || !commitSha) return;
    if (!activePath) {
      setContent('');
      return;
    }
    (async () => {
      try {
        const res = await fetch(`/api/docs/file?kbId=${encodeURIComponent(kbId)}&commitSha=${encodeURIComponent(commitSha)}&path=${encodeURIComponent(activePath)}`, { cache: 'no-store' });
        const data = await res.json();
        setContent(data?.content || '');
      } catch {
        setContent('');
      }
    })();
  }, [kbId, commitSha, activePath]);

  useEffect(() => {
    if (!activePath && fileList.length > 0) {
      setActivePath(fileList[0]);
    }
  }, [fileList, activePath]);

  useEffect(() => {
    const container = contentRef.current;
    if (!container || !content) {
      setToc([]);
      return;
    }

    const headingElements = Array.from(container.querySelectorAll<HTMLElement>('h1, h2, h3'));
    const slugCounts = new Map<string, number>();
    const headings = headingElements.map((el) => {
      const text = el.textContent?.trim() ?? '';
      if (!text) return null;

      const base = slugify(text);
      if (!base) return null;

      const existing = slugCounts.get(base) ?? 0;
      slugCounts.set(base, existing + 1);
      const id = existing === 0 ? base : `${base}-${existing + 1}`;
      el.id = id;
      el.tabIndex = -1;

      return {
        id,
        text,
        level: Number(el.tagName.replace('H', '')),
      };
    }).filter((item): item is { id: string; text: string; level: number } => !!item);

    setToc(headings);

    const pendingHighlight = highlightTermRef.current?.trim();
    if (pendingHighlight) {
      highlightTermRef.current = null;
      highlightInContent(pendingHighlight);
    }
  }, [content]);

  // Provide a link click handler to Markdown so relative links work inside content and index
  const handleMarkdownLink = useCallback((href: string) => {
    const normalized = href.replace(/^\.\//, '').replace(/^\//, '');
    setActivePath(normalized);
    setResults([]);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [setActivePath, setResults]);

  useEffect(() => {
    const container = contentRef.current;
    if (!container) return;

    const handleClick = (event: MouseEvent) => {
      if (event.defaultPrevented) return;
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;

      const target = event.target as HTMLElement | null;
      if (!target) return;

      const anchor = target.closest('a');
      if (!anchor) return;

      const href = anchor.getAttribute('href');
      if (!href) return;
      if (href.startsWith('http') || href.startsWith('#') || href.startsWith('mailto:')) return;

      event.preventDefault();
      handleMarkdownLink(href);
    };

    container.addEventListener('click', handleClick);
    return () => container.removeEventListener('click', handleClick);
  }, [handleMarkdownLink]);

  const doSearch = async () => {
    if (!kbId || !commitSha || !q.trim()) return;
    setSearching(true);
    try {
      const res = await fetch(`/api/docs/search?kbId=${encodeURIComponent(kbId)}&commitSha=${encodeURIComponent(commitSha)}&q=${encodeURIComponent(q)}`, { cache: 'no-store' });
      const data = await res.json();
      setResults(data?.results || []);
    } finally {
      setSearching(false);
    }
  };

  const resetSearchState = useCallback((options?: { keepQuery?: boolean }) => {
    setIsSearchOpen(false);
    setSelectedIdx(0);
    setResults([]);
    setSearching(false);
    if (!options?.keepQuery) {
      setQ('');
    }
  }, []);

  const handleResultActivate = useCallback((path: string) => {
    const term = q.trim();
    if (term) {
      highlightTermRef.current = term;
    }
    setActivePath(path);
    resetSearchState();
  }, [q, resetSearchState]);

  // Debounced live search after 3 chars
  useEffect(() => {
    if (!q || q.length < 3) {
      setResults([]);
      setSearching(false);
      return;
    }
    const id = setTimeout(() => {
      doSearch();
    }, 250);
    return () => clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q, kbId, commitSha]);

  useEffect(() => {
    const handleShortcut = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        if (isSearchOpen) {
          resetSearchState();
        } else {
          setIsSearchOpen(true);
        }
      }
    };

    window.addEventListener('keydown', handleShortcut);
    return () => window.removeEventListener('keydown', handleShortcut);
  }, [isSearchOpen, resetSearchState]);

  useEffect(() => {
    if (!isSearchOpen) return;

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        resetSearchState();
      }
    };

    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [isSearchOpen, resetSearchState]);

  useEffect(() => {
    if (!isSearchOpen) return;

    const timer = window.setTimeout(() => {
      searchInputRef.current?.focus();
      searchInputRef.current?.select();
    }, 80);

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    return () => {
      window.clearTimeout(timer);
      document.body.style.overflow = previousOverflow;
    };
  }, [isSearchOpen]);

  const hasVersions = versions.length > 0;
  const showVersionSelector = !!kbId && (hasVersions || !!commitSha);

  const slugify = (value: string) => {
    return value
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-');
  };

  const escapeRegExp = (value: string) => value.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&');

  const highlightInContent = (term: string) => {
    const normalized = term.trim();
    if (!normalized) return;

    const container = contentRef.current;
    if (!container) return;

    container.querySelectorAll('.doc-flash').forEach((el) => el.classList.remove('doc-flash'));

    requestAnimationFrame(() => {
      const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
      const regex = new RegExp(escapeRegExp(normalized), 'i');
      let node: Node | null;

      while ((node = walker.nextNode())) {
        const textNode = node as Text;
        if (!textNode?.nodeValue) continue;
        if (!regex.test(textNode.nodeValue)) continue;

        const element = textNode.parentElement as HTMLElement | null;
        if (!element) break;

        element.classList.add('doc-flash');
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setTimeout(() => element.classList.remove('doc-flash'), 1200);
        break;
      }
    });
  };

  const handleTocNavigate = (id: string) => {
    const el = document.getElementById(id);
    if (!el) return;

    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    const isFocusable = 'focus' in el;
    if (isFocusable) {
      (el as HTMLElement).focus({ preventScroll: true });
    }
  };

  const versionSelector = showVersionSelector ? (
    <div className="flex items-center gap-2">
      <Select value={commitSha} onValueChange={(v) => setCommitSha(v)} disabled={!hasVersions}>
        <SelectTrigger className="w-[220px]" title={commitSha || undefined}>
          <SelectValue placeholder={hasVersions ? 'Select version' : 'No versions'} />
        </SelectTrigger>
        {hasVersions && (
          <SelectContent>
            {versions.map(v => (
              <SelectItem key={v} value={v}>{v.slice(0, 7)}</SelectItem>
            ))}
          </SelectContent>
        )}
      </Select>
      {commitSha && (
        <Button
          type="button"
          variant="outline"
          size="icon"
          title={`Copy full SHA: ${commitSha}`}
          onClick={() => navigator.clipboard.writeText(commitSha)}
          className="h-8 w-8"
        >
          <CopyIcon size={16} />
          <span className="sr-only">Copy commit</span>
        </Button>
      )}
    </div>
  ) : undefined;

  const trimmedQuery = q.trim();
  const hasSearchQuery = trimmedQuery.length >= 3;
  const displayedItems = hasSearchQuery
    ? results.map((r) => ({
      key: `${r.path}-${r.line ?? 0}`,
      path: r.path,
      title: titleMap[r.path] || r.path,
      snippet: r.snippet || r.path,
    }))
    : fileList.slice(0, 10).map((path) => ({
      key: path,
      path,
      title: titleMap[path] || path,
      snippet: path,
    }));

  return (
    <div className="flex flex-col min-w-0 h-dvh bg-background">
      <SharedHeader rightExtra={
        <div className="hidden md:flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Version</span>
            {versionSelector}
          </div>
        </div>
      }>
        <div className="flex flex-1 items-center gap-3 px-2 md:px-4">
          <span className="text-lg lg:text-xl font-semibold text-foreground truncate">Docs</span>
          <button
            type="button"
            onClick={() => setIsSearchOpen(true)}
            className="hidden md:flex flex-1 items-center gap-3 max-w-md rounded-lg border border-border bg-muted/60 px-3 py-2 text-sm text-muted-foreground shadow-sm transition hover:bg-muted"
          >
            <SearchIcon size={16} className="text-muted-foreground" />
            <span className="flex-1 truncate text-left">Search docs</span>
            <span className="text-xs font-medium text-muted-foreground/80">⌘K</span>
          </button>
          <Button
            type="button"
            variant="outline"
            size="icon"
            className="md:hidden"
            onClick={() => setIsSearchOpen(true)}
          >
            <SearchIcon size={16} />
            <span className="sr-only">Search docs</span>
          </Button>
        </div>
      </SharedHeader>
      <div className="flex-1 overflow-auto">
        <div className="mx-auto w-full max-w-[1400px] px-4 sm:px-6 lg:px-8 py-8">
          {!kbId ? (
            <div className="border rounded-md p-6 text-center text-muted-foreground">No knowledge base configured for this space.</div>
          ) : !commitSha ? (
            <div className="border rounded-md p-6 text-center text-muted-foreground">No docs available yet.</div>
          ) : (
            <div className="flex flex-col gap-8 lg:grid lg:grid-cols-[minmax(0,260px)_minmax(0,1fr)_minmax(0,220px)]">
              <aside className="lg:sticky lg:top-24 h-fit space-y-4">
                <div className="rounded-xl border bg-card/50 backdrop-blur">
                  <div className="px-4 py-3 border-b">
                    <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Index</span>
                  </div>
                  <div className="px-2 py-3">
                    <div className="space-y-1">
                      {fileList.map((f) => (
                        <button
                          key={f}
                          className={`w-full rounded-lg px-3 py-2 text-left text-sm transition-colors hover:bg-muted/50 ${activePath === f ? 'bg-muted text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
                          onClick={() => handleMarkdownLink(f)}
                        >
                          <span className="block truncate font-medium">{titleMap[f] || f}</span>
                          <span className="block text-xs text-muted-foreground/80 truncate">{f}</span>
                        </button>
                      ))}
                      {fileList.length === 0 && (
                        <div className="rounded-md bg-muted/50 px-3 py-4 text-xs text-muted-foreground">No files found.</div>
                      )}
                    </div>
                  </div>
                </div>
              </aside>

              <main className="min-w-0">
                <div className="mx-auto max-w-3xl rounded-2xl border bg-card/70 p-6 shadow-sm" ref={contentRef}>
                  {activePath ? (
                    content ? (
                      <div className="prose prose-neutral dark:prose-invert max-w-none">
                        <Markdown>{content}</Markdown>
                      </div>
                    ) : (
                      <div className="text-sm text-muted-foreground">Loading…</div>
                    )
                  ) : (
                    <div className="text-sm text-muted-foreground">Select a document from the index.</div>
                  )}
                </div>
              </main>

              <aside className="hidden lg:block lg:sticky lg:top-24 h-fit">
                <div className="rounded-xl border bg-card/50 p-4">
                  <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">On this page</span>
                  <div className="mt-3 space-y-1 text-sm">
                    {toc.length > 0 ? (
                      toc.map((item) => {
                        const indent = item.level >= 3 ? 'pl-6' : item.level === 2 ? 'pl-3' : '';
                        const subdued = item.level >= 3 ? 'text-muted-foreground/70' : 'text-muted-foreground';
                        return (
                          <button
                            key={item.id}
                            type="button"
                            onClick={() => handleTocNavigate(item.id)}
                            className={`block w-full rounded-md px-2 py-1 text-left transition-colors hover:bg-muted/50 hover:text-foreground ${indent} ${subdued}`}
                          >
                            {item.text}
                          </button>
                        );
                      })
                    ) : (
                      <div className="rounded-md bg-muted/40 px-3 py-4 text-xs text-muted-foreground">No headings yet.</div>
                    )}
                  </div>
                </div>
              </aside>
            </div>
          )}
        </div>
      </div>
      {isSearchOpen && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center bg-background/80 backdrop-blur-sm px-4 pt-24"
          role="dialog"
          aria-modal="true"
          onClick={() => resetSearchState()}
        >
          <div
            className="w-full max-w-2xl overflow-hidden rounded-2xl border border-border bg-card shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-center gap-3 border-b border-border/80 px-4 py-3">
              <SearchIcon size={18} className="text-muted-foreground" />
              <Input
                ref={searchInputRef}
                value={q}
                placeholder="Search docs..."
                onChange={(event) => {
                  setQ(event.target.value);
                  setSelectedIdx(0);
                }}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') {
                    event.preventDefault();
                    if (trimmedQuery.length < 3 && results.length === 0 && displayedItems.length === 0) {
                      void doSearch();
                      return;
                    }
                    const target = displayedItems[Math.min(selectedIdx, Math.max(0, displayedItems.length - 1))];
                    if (target) {
                      handleResultActivate(target.path);
                    }
                  } else if (event.key === 'ArrowDown') {
                    event.preventDefault();
                    setSelectedIdx((index) => Math.min(index + 1, Math.max(0, displayedItems.length - 1)));
                  } else if (event.key === 'ArrowUp') {
                    event.preventDefault();
                    setSelectedIdx((index) => Math.max(index - 1, 0));
                  }
                }}
                className="h-11 border-0 bg-transparent px-0 text-base focus-visible:ring-0"
                autoFocus
              />
              <span className="hidden items-center gap-1 rounded-md border bg-muted px-2 py-1 text-[10px] font-medium text-muted-foreground/80 sm:inline-flex">
                Esc
              </span>
            </div>
            <div className="px-4 pt-3 text-xs font-medium uppercase tracking-wide text-muted-foreground/80">
              {hasSearchQuery ? 'Results' : 'Suggested'}
            </div>
            <div className="max-h-[320px] overflow-y-auto py-2">
              {searching ? (
                <div className="px-4 py-6 text-sm text-muted-foreground">Searching…</div>
              ) : displayedItems.length > 0 ? (
                displayedItems.map((item, index) => (
                  <button
                    key={item.key}
                    type="button"
                    onClick={() => handleResultActivate(item.path)}
                    onMouseEnter={() => setSelectedIdx(index)}
                    className={`flex w-full flex-col items-start gap-1 px-4 py-3 text-left transition-colors hover:bg-muted/60 ${index === selectedIdx ? 'bg-muted text-foreground' : 'text-muted-foreground'}`}
                  >
                    <span className="text-sm font-medium text-foreground">{item.title}</span>
                    {item.snippet && (
                      <span className="text-xs text-muted-foreground/80 truncate">{item.snippet}</span>
                    )}
                  </button>
                ))
              ) : (
                <div className="px-4 py-10 text-center text-sm text-muted-foreground">
                  {hasSearchQuery
                    ? 'No matches found.'
                    : trimmedQuery.length > 0
                      ? 'Type at least 3 characters to search.'
                      : fileList.length === 0
                        ? 'No documents available yet.'
                        : 'Start typing to search docs.'}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      {/* flash highlight styling and auto-clear */}
      <style>
        {`
        .doc-flash { animation: docFlash 1.2s ease-in-out 1; background-color: rgba(250, 229, 150, 0.9); }
        @keyframes docFlash { 0% { background-color: rgba(250,229,150,0.9); } 100% { background-color: transparent; } }
        `}
      </style>
    </div>
  );
}
