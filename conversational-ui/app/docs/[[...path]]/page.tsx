"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { SharedHeader } from '@/components/shared-header';
import { Markdown } from '@/components/markdown';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { SearchIcon, CopyIcon } from '@/components/icons';
import { useSession } from 'next-auth/react';
import { useRouter, useParams, useSearchParams } from 'next/navigation';
import { Input } from '@/components/ui/input';

export default function DocsPage() {
  const { data: session } = useSession();
  const router = useRouter();
  const params = useParams<{ path?: string[] }>();
  const searchParams = useSearchParams();
  const kbId = session?.user?.selectedSpace?.knowledgeBaseId;
  // commit sha is not currently typed on selectedSpace; leave undefined and rely on versions API
  const currentCommit = undefined as string | undefined;

  const [commitSha, setCommitSha] = useState<string | undefined>(currentCommit);
  const [versions, setVersions] = useState<string[]>([]);
  const [, setIndexMd] = useState<string>('');
  const [fileList, setFileList] = useState<string[]>([]);
  const [titleMap, setTitleMap] = useState<Record<string, string>>({});
  const [activePath, setActivePathState] = useState<string | null>(null);
  const [content, setContent] = useState<string>('');
  const [contentStatus, setContentStatus] = useState<'idle' | 'loading' | 'ready' | 'missing'>('idle');
  const [q, setQ] = useState('');
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<{ path: string; snippet: string; line?: number; occurrence?: number; offset?: number }[]>([]);
  const [selectedIdx, setSelectedIdx] = useState<number>(0);
  const contentRef = useRef<HTMLDivElement | null>(null);
  const [toc, setToc] = useState<{ id: string; text: string; level: number }[]>([]);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const searchInputRef = useRef<HTMLInputElement | null>(null);
  const resultsContainerRef = useRef<HTMLDivElement | null>(null);
  const highlightTermRef = useRef<{ term: string; occurrence?: number } | null>(null);
  const lastCommitRef = useRef<string | undefined>(commitSha);
  const pathSegments = Array.isArray(params?.path) ? params.path : [];
  const pathParam = pathSegments.length > 0 ? pathSegments.map(segment => decodeURIComponent(segment)).join('/') : null;
  const versionParam = searchParams?.get('v')?.trim() ?? null;
  const normalizedVersionParam = versionParam ? versionParam.toLowerCase() : null;
  const shortCommit = useMemo(() => (commitSha ? commitSha.slice(0, 7) : null), [commitSha]);

  const highlightInContent = useCallback(({ term, occurrence }: { term: string; occurrence?: number }) => {
    const normalized = term.trim();
    if (!normalized) return;

    const container = contentRef.current;
    if (!container) return;

    container.querySelectorAll('.doc-flash').forEach((el) => el.classList.remove('doc-flash'));

    requestAnimationFrame(() => {
      const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
      const searchTerm = normalized.toLowerCase();
      const targetOccurrence = occurrence ?? 0;
      let matchIndex = 0;
      let node: Node | null;

      while ((node = walker.nextNode())) {
        const textNode = node as Text;
        const nodeValue = textNode?.nodeValue;
        if (!nodeValue) continue;

        const lowerValue = nodeValue.toLowerCase();
        let fromIndex = 0;

        while (true) {
          const foundIndex = lowerValue.indexOf(searchTerm, fromIndex);
          if (foundIndex === -1) break;

          if (matchIndex === targetOccurrence) {
            const element = textNode.parentElement as HTMLElement | null;
            if (!element) return;

            element.classList.add('doc-flash');
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
            window.setTimeout(() => element.classList.remove('doc-flash'), 1200);
            return;
          }

          matchIndex += 1;
          fromIndex = foundIndex + searchTerm.length;
        }
      }
    });
  }, [contentRef]);

  useEffect(() => {
    setActivePathState(pathParam ?? null);
  }, [pathParam]);

  const encodePath = useCallback((value: string) => value.split('/').map(segment => encodeURIComponent(segment)).join('/'), []);

  const setActivePath = useCallback((next: string | null, options?: { replace?: boolean; versionOverride?: string | null }) => {
    setActivePathState(prev => (prev === next ? prev : next));
    const baseUrl = next ? `/docs/${encodePath(next)}` : '/docs';
    const versionToken = options?.versionOverride ?? shortCommit;
    const url = versionToken ? `${baseUrl}?v=${encodeURIComponent(versionToken)}` : baseUrl;
    if (options?.replace) {
      router.replace(url, { scroll: false });
    } else {
      router.push(url, { scroll: false });
    }
    if (typeof window !== 'undefined') {
      window.history.replaceState(null, '', url);
    }
  }, [router, encodePath, shortCommit]);

  const groupedFiles = useMemo(() => {
    const groups = new Map<string, { path: string; title: string }[]>();
    for (const path of fileList) {
      const parts = path.split('/');
      const group = parts.length > 1 ? parts.slice(0, -1).join('/') : '';
      if (!groups.has(group)) groups.set(group, []);
      groups.get(group)!.push({ path, title: titleMap[path] || path });
    }

    const toLabel = (key: string) => {
      if (!key) return '';
      return key
        .split('/')
        .map(segment => segment
          .replace(/[-_]+/g, ' ')
          .replace(/\b\w/g, char => char.toUpperCase())
        )
        .join(' / ');
    };

    const entries = Array.from(groups.entries()).map(([group, items]) => ({
      group,
      label: toLabel(group),
      entries: items.sort((a, b) => a.title.localeCompare(b.title, undefined, { sensitivity: 'base' })),
    }));

    entries.sort((a, b) => {
      if (a.group === '') return -1;
      if (b.group === '') return 1;
      return a.label.localeCompare(b.label, undefined, { sensitivity: 'base' });
    });

    return entries;
  }, [fileList, titleMap]);

  // Load versions on mount and pick commit based on URL query when possible
  useEffect(() => {
    if (!kbId) return;
    (async () => {
      try {
        const res = await fetch(`/api/docs/versions?kbId=${encodeURIComponent(kbId)}`, { cache: 'no-store' });
        const data = await res.json();
        if (Array.isArray(data.versions)) {
          setVersions(data.versions);
          const matchedFromQuery = normalizedVersionParam
            ? data.versions.find((sha: string) => sha.toLowerCase().startsWith(normalizedVersionParam))
            : undefined;
          setCommitSha((prev) => {
            if (matchedFromQuery) return matchedFromQuery;
            if (prev && data.versions.includes(prev)) return prev;
            return data.versions.length > 0 ? data.versions[data.versions.length - 1] : undefined;
          });
        }
      } catch {}
    })();
  }, [kbId, normalizedVersionParam]);

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
      setContentStatus('idle');
      return;
    }
    let aborted = false;
    setContent('');
    setContentStatus('loading');
    (async () => {
      try {
        const res = await fetch(`/api/docs/file?kbId=${encodeURIComponent(kbId)}&commitSha=${encodeURIComponent(commitSha)}&path=${encodeURIComponent(activePath)}`, { cache: 'no-store' });
        if (!res.ok) throw new Error('Failed to load doc');
        const data = await res.json();
        if (aborted) return;
        const nextContent = typeof data?.content === 'string' ? data.content : '';
        setContent(nextContent);
        setContentStatus('ready');
      } catch {
        if (aborted) return;
        setContent('');
        setContentStatus('missing');
      }
    })();
    return () => {
      aborted = true;
    };
  }, [kbId, commitSha, activePath]);

  useEffect(() => {
    if (lastCommitRef.current === commitSha) return;
    lastCommitRef.current = commitSha;
    setActivePath(activePath, { replace: true });
  }, [commitSha, activePath, setActivePath]);

  useEffect(() => {
    if (!pathParam && fileList.length > 0) {
      setActivePath(fileList[0], { replace: true });
    }
  }, [fileList, pathParam, setActivePath]);

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

    const pendingHighlight = highlightTermRef.current;
    if (pendingHighlight?.term.trim()) {
      highlightTermRef.current = null;
      highlightInContent(pendingHighlight);
    }
  }, [content, highlightInContent]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const hash = window.location.hash.slice(1);
    if (!hash) return;
    const el = document.getElementById(hash);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [content, activePath]);

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

  const handleResultActivate = useCallback((path: string, occurrence?: number) => {
    const term = q.trim();
    if (term) {
      const highlightPayload = { term, occurrence } as const;
      highlightTermRef.current = highlightPayload;
      if (path === activePath) {
        highlightInContent(highlightPayload);
        resetSearchState();
        return;
      }
    }
    setActivePath(path);
    resetSearchState();
  }, [activePath, highlightInContent, q, resetSearchState, setActivePath]);

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
  const latestCommitSha = hasVersions ? versions[versions.length - 1] : undefined;
  const orderedVersions = hasVersions ? [...versions].reverse() : [];
  const isLatestCommit = !!commitSha && !!latestCommitSha && commitSha === latestCommitSha;
  const truncatedCommitSha = commitSha ? commitSha.slice(0, 7) : '';
  const showVersionSelector = !!kbId && (hasVersions || !!commitSha);

  const slugify = (value: string) => {
    return value
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-');
  };

  const handleTocNavigate = (id: string) => {
    const el = document.getElementById(id);
    if (!el) return;

    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    const isFocusable = 'focus' in el;
    if (isFocusable) {
      (el as HTMLElement).focus({ preventScroll: true });
    }
    if (typeof window !== 'undefined') {
      const base = activePath ? `/docs/${encodePath(activePath)}` : '/docs';
      const versionToken = shortCommit ? `?v=${encodeURIComponent(shortCommit)}` : '';
      window.history.replaceState(null, '', `${base}${versionToken}#${id}`);
    }
  };

  const versionSelector = showVersionSelector ? (
    <div className="flex items-center gap-1.5">
      <Select
        value={commitSha}
        onValueChange={(v) => setCommitSha(v)}
        disabled={!hasVersions}
      >
        <SelectTrigger
          className="h-9 min-w-[150px] px-3 py-1.5"
          title={commitSha ? (isLatestCommit ? `Latest (${commitSha})` : commitSha) : undefined}
        >
          {commitSha ? (
            <div className="flex items-baseline gap-2">
              <span className="text-sm font-semibold text-foreground">
                {isLatestCommit ? 'Latest' : truncatedCommitSha}
              </span>
              {isLatestCommit && (
                <span className="font-mono text-xs text-muted-foreground/80">
                  {truncatedCommitSha}
                </span>
              )}
            </div>
          ) : (
            <SelectValue placeholder={hasVersions ? 'Select version' : 'No versions'} />
          )}
        </SelectTrigger>
        {hasVersions && (
          <SelectContent>
            {orderedVersions.map((v) => {
              const isLatestOption = latestCommitSha === v;
              const shortHash = v.slice(0, 7);
              return (
                <SelectItem key={v} value={v}>
                  <div className="flex items-baseline gap-2">
                    <span className="text-sm font-medium text-foreground">
                      {isLatestOption ? 'Latest' : shortHash}
                    </span>
                    {isLatestOption && (
                      <span className="font-mono text-xs text-muted-foreground/80">
                        {shortHash}
                      </span>
                    )}
                  </div>
                </SelectItem>
              );
            })}
          </SelectContent>
        )}
      </Select>
      {commitSha && (
        <Button
          type="button"
          variant="outline"
          size="icon"
          title={`Copy full SHA: ${commitSha}`}
          aria-label="Copy commit SHA"
          onClick={() => navigator.clipboard.writeText(commitSha)}
          className="h-6 w-6 text-muted-foreground"
        >
          <CopyIcon size={12} />
        </Button>
      )}
    </div>
  ) : undefined;

  const trimmedQuery = q.trim();
  const hasSearchQuery = trimmedQuery.length >= 3;
  const displayedItems = hasSearchQuery
    ? results.map((r) => ({
      key: `${r.path}-${r.offset ?? r.occurrence ?? r.line ?? 0}`,
      path: r.path,
      title: titleMap[r.path] || r.path,
      snippet: r.snippet || r.path,
      occurrence: r.occurrence,
    }))
    : fileList.slice(0, 10).map((path) => ({
      key: path,
      path,
      title: titleMap[path] || path,
      snippet: path,
      occurrence: undefined,
    }));

  const scrollResultIntoView = useCallback((index: number) => {
    if (index < 0) return;
    requestAnimationFrame(() => {
      const container = resultsContainerRef.current;
      if (!container) return;
      const target = container.querySelector<HTMLButtonElement>(`[data-result-index="${index}"]`);
      if (!target) return;
      target.scrollIntoView({ block: 'nearest' });
    });
  }, []);

  useEffect(() => {
    if (!isSearchOpen) return;
    scrollResultIntoView(Math.min(selectedIdx, Math.max(displayedItems.length - 1, 0)));
  }, [displayedItems.length, isSearchOpen, scrollResultIntoView, selectedIdx]);

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
        <div className="mx-auto w-full max-w-[1440px] px-4 sm:px-6 lg:px-8 py-6">
          {!kbId ? (
            <div className="border rounded-md p-6 text-center text-muted-foreground">No knowledge base configured for this space.</div>
          ) : !commitSha ? (
            <div className="border rounded-md p-6 text-center text-muted-foreground">No docs available yet.</div>
          ) : (
            <div className="flex flex-col gap-6 lg:grid lg:grid-cols-[minmax(0,260px)_minmax(0,1fr)_minmax(0,240px)]">
              <aside className="lg:sticky lg:top-24 h-fit text-sm">
                <div className="docs-index max-h-[calc(100vh-10rem)] overflow-y-auto pr-1 space-y-5">
                  {groupedFiles.length === 0 ? (
                    <div className="px-3 py-2 text-xs text-muted-foreground">No files found.</div>
                  ) : (
                    groupedFiles.map(({ group, label, entries }) => {
                      if (!label) {
                        return (
                          <div key="__root" className="space-y-1">
                            {entries.map(({ path: filePath, title }) => (
                              <button
                                key={filePath}
                                className={`flex w-full flex-col rounded-md px-3 py-2 text-left transition-colors ${activePath === filePath ? 'text-primary font-semibold' : 'text-muted-foreground hover:text-foreground'}`}
                                onClick={() => handleMarkdownLink(filePath)}
                              >
                                <span className="text-sm leading-snug">{title}</span>
                                <span className="text-[11px] text-muted-foreground/70 leading-tight">{filePath}</span>
                              </button>
                            ))}
                          </div>
                        );
                      }

                      return (
                        <details key={group} className="group space-y-1" open>
                          <summary className="flex cursor-pointer items-center justify-between px-3 py-1 text-sm font-semibold text-foreground list-none">
                            <span>{label}</span>
                            <ChevronDown
                              aria-hidden="true"
                              className="docs-index-caret h-4 w-4 text-muted-foreground/60 transition-transform duration-200 group-open:rotate-180"
                            />
                          </summary>
                          <div className="mt-1 space-y-1 pl-3">
                            {entries.map(({ path: filePath, title }) => (
                              <button
                                key={filePath}
                                className={`flex w-full flex-col rounded-md px-3 py-2 text-left transition-colors ${activePath === filePath ? 'text-primary font-semibold' : 'text-muted-foreground hover:text-foreground'}`}
                                onClick={() => handleMarkdownLink(filePath)}
                              >
                                <span className="text-sm leading-snug">{title}</span>
                                <span className="text-[11px] text-muted-foreground/70 leading-tight">{filePath}</span>
                              </button>
                            ))}
                          </div>
                        </details>
                      );
                    })
                  )}
                </div>
              </aside>

              <main className="min-w-0">
                <div className="mx-auto max-w-7xl px-2 sm:px-4" ref={contentRef}>
                  {activePath ? (
                    contentStatus === 'ready' ? (
                      <div className="prose prose-neutral dark:prose-invert max-w-none">
                        <Markdown>{content}</Markdown>
                      </div>
                    ) : contentStatus === 'missing' ? (
                      <div className="rounded-md border border-dashed border-border/80 bg-muted/30 px-4 py-5 text-sm text-muted-foreground">
                        We couldn’t find this document in the selected version. Try another version or pick a different doc.
                      </div>
                    ) : (
                      <div className="text-sm text-muted-foreground">Loading…</div>
                    )
                  ) : (
                    <div className="text-sm text-muted-foreground">Select a document from the index.</div>
                  )}
                </div>
              </main>

              <aside className="hidden lg:block lg:sticky lg:top-24 h-fit text-xs">
                <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground/80">On this page</div>
                <div className="mt-3 max-h-[calc(100vh-10rem)] overflow-y-auto pr-1 space-y-[2px]">
                  {toc.length > 0 ? (
                    toc.map((item) => {
                      const indent = item.level >= 3 ? 'pl-5' : item.level === 2 ? 'pl-3' : '';
                      return (
                        <div key={item.id} className={indent}>
                          <button
                            type="button"
                            onClick={() => handleTocNavigate(item.id)}
                            className="group relative flex w-full items-start rounded-md px-2 py-[5px] text-left text-muted-foreground transition-colors hover:bg-muted/30 hover:text-foreground"
                          >
                            <span className="block text-[12px] leading-5 whitespace-normal break-words">{item.text}</span>
                            <span className="pointer-events-none absolute left-full top-1/2 z-10 hidden min-w-[260px] -translate-y-1/2 translate-x-3 rounded-md border border-border/70 bg-background/95 px-2 py-1 text-[11px] text-foreground shadow-sm group-hover:flex dark:bg-background/90">
                              {item.text}
                            </span>
                          </button>
                        </div>
                      );
                    })
                  ) : (
                    <div className="rounded-md bg-muted/40 px-3 py-4 text-xs text-muted-foreground">No headings yet.</div>
                  )}
                </div>
              </aside>
            </div>
          )}
        </div>
      </div>
      {isSearchOpen && (
        <div
          className="docs-search-overlay fixed inset-0 z-50 flex items-start justify-center bg-black/10 backdrop-blur-3xl backdrop-saturate-150 px-4 pt-20 dark:bg-black/40"
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
                          handleResultActivate(target.path, target.occurrence);
                        }
                      } else if (event.key === 'ArrowDown') {
                        event.preventDefault();
                        const nextIndex = Math.min(selectedIdx + 1, Math.max(0, displayedItems.length - 1));
                        setSelectedIdx(nextIndex);
                        scrollResultIntoView(nextIndex);
                      } else if (event.key === 'ArrowUp') {
                        event.preventDefault();
                        const nextIndex = Math.max(selectedIdx - 1, 0);
                        setSelectedIdx(nextIndex);
                        scrollResultIntoView(nextIndex);
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
            <div
              ref={resultsContainerRef}
              className="max-h-[320px] overflow-y-auto py-2"
            >
              {searching ? (
                <div className="px-4 py-6 text-sm text-muted-foreground">Searching…</div>
              ) : displayedItems.length > 0 ? (
                displayedItems.map((item, index) => (
                  <button
                    key={item.key}
                    type="button"
                    onClick={() => handleResultActivate(item.path, item.occurrence)}
                    onMouseEnter={() => {
                      setSelectedIdx(index);
                      scrollResultIntoView(index);
                    }}
                    data-result-index={index}
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
        .docs-index details summary { list-style: none; border: none; outline: none; border-radius: 0; background: transparent; }
        .docs-index details summary:focus-visible,
        .docs-index details summary:focus { outline: none !important; border: none !important; box-shadow: none !important; background: transparent; }
        .docs-index details summary::after { display: none; }
        .docs-index details summary::-webkit-details-marker { display: none; }
        `}
      </style>
    </div>
  );
}
