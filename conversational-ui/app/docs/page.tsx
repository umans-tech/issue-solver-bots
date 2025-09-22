"use client";

import { useEffect, useRef, useState } from 'react';
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
  const [, setSearching] = useState(false);
  const [results, setResults] = useState<{ path: string; snippet: string; line?: number }[]>([]);
  const [selectedIdx, setSelectedIdx] = useState<number>(0);
  const contentRef = useRef<HTMLDivElement | null>(null);

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

  // Provide a link click handler to Markdown so relative links work inside content and index
  const handleMarkdownLink = (href: string) => {
    const normalized = href.replace(/^\.\//, '').replace(/^\//, '');
    setActivePath(normalized);
    setResults([]);
    window.scrollTo({ top: 0 });
  };

  const interceptRelative = (href: string) => {
    const normalized = href.replace(/^\.\//, '').replace(/^\//, '');
    setActivePath(normalized);
    setResults([]);
    window.scrollTo({ top: 0 });
  };

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

  // Debounced live search after 3 chars
  useEffect(() => {
    if (!q || q.length < 3) {
      setResults([]);
      return;
    }
    const id = setTimeout(() => {
      doSearch();
    }, 250);
    return () => clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q, kbId, commitSha]);

  const hasVersions = versions.length > 0;
  const showVersionSelector = !!kbId && (hasVersions || !!commitSha);

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
        <div className="flex items-center gap-3 text-sm min-w-0">
          <span className="text-lg lg:text-xl font-semibold text-foreground truncate">Docs</span>
        </div>
      </SharedHeader>
      <div className="flex-1 overflow-auto">
        <div className="container mx-auto py-6 px-4 lg:px-6">
          {!kbId ? (
            <div className="border rounded-md p-6 text-center text-muted-foreground">No knowledge base configured for this space.</div>
          ) : !commitSha ? (
            <div className="border rounded-md p-6 text-center text-muted-foreground">No docs available yet.</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="md:col-span-1 space-y-4">
                {/* Unified Search Card */}
                <div className="rounded-md border">
                  <div className="p-2 border-b text-xs text-muted-foreground flex items-center justify-between">
                    <span>Search</span>
                    <Button variant="ghost" size="sm" onClick={() => { setQ(''); setResults([]); setSelectedIdx(0); }}>
                      Clear
                    </Button>
                  </div>
                  <div className="p-2">
                    <div className="relative mb-2">
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                        <SearchIcon size={16} />
                      </span>
                      <Input
                        placeholder="Search docs..."
                        value={q}
                        onChange={(e) => { setQ(e.target.value); setSelectedIdx(0); }}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            if (q.trim().length < 3 && results.length === 0) {
                              doSearch();
                            } else if (results.length > 0) {
                              const r = results[Math.min(selectedIdx, results.length - 1)];
                              if (r) {
                                setActivePath(r.path);
                                setTimeout(() => {
                                  requestAnimationFrame(() => {
                                    const container = contentRef.current;
                                    if (container) {
                                      const text = q.trim();
                                      if (text) {
                                        const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
                                        let node: any;
                                        const regex = new RegExp(text.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&'), 'i');
                                        while ((node = walker.nextNode())) {
                                          if (regex.test(node.nodeValue || '')) {
                                            const el = node.parentElement as HTMLElement;
                                            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                            break;
                                          }
                                        }
                                      }
                                    }
                                  });
                                }, 250);
                                setResults([]);
                              }
                            }
                          } else if (e.key === 'ArrowDown') {
                            e.preventDefault();
                            setSelectedIdx((i) => Math.min(i + 1, Math.max(0, results.length - 1)));
                          } else if (e.key === 'ArrowUp') {
                            e.preventDefault();
                            setSelectedIdx((i) => Math.max(i - 1, 0));
                          }
                        }}
                        className="pl-9"
                      />
                    </div>
                    <div className="max-h-[260px] overflow-auto divide-y">
                      {(results.length > 0 ? results : []).map((r, i) => (
                        <button
                          key={i}
                          className={`w-full text-left p-3 hover:bg-muted/50 ${i === selectedIdx ? 'bg-muted' : ''}`}
                          onClick={() => {
                            setActivePath(r.path);
                            setTimeout(() => {
                              requestAnimationFrame(() => {
                                const container = contentRef.current;
                                if (container) {
                                  const text = q.trim();
                                  if (text) {
                                    const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
                                    let node: any;
                                    const regex = new RegExp(text.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&'), 'i');
                                    while ((node = walker.nextNode())) {
                                      if (regex.test(node.nodeValue || '')) {
                                        const el = node.parentElement as HTMLElement;
                                        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                        break;
                                      }
                                    }
                                  }
                                }
                              });
                            }, 250);
                            setResults([]);
                          }}
                        >
                          <div className="text-sm font-medium truncate">{r.path}</div>
                          <div className="text-xs text-muted-foreground truncate">{r.snippet}</div>
                        </button>
                      ))}
                      {results.length === 0 && (
                        <div className="px-3 py-6 text-xs text-muted-foreground">Type 3+ characters to search. Press Enter to force search.</div>
                      )}
                    </div>
                  </div>
                </div>
                <div className="rounded-md border">
                  <div className="p-2 border-b text-xs text-muted-foreground flex items-center justify-between">
                    <span>Index</span>
                  </div>
                  <div className="p-2">
                    <div className="space-y-1">
                      {fileList.map((f) => (
                        <button
                          key={f}
                          className={`w-full text-left px-2 py-1 rounded hover:bg-muted/50 text-sm ${activePath === f ? 'bg-muted' : ''}`}
                          onClick={() => setActivePath(f)}
                        >
                          {titleMap[f] || f}
                        </button>
                      ))}
                      {fileList.length === 0 && (
                        <div className="text-xs text-muted-foreground p-2">No files found.</div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
              <div className="md:col-span-2">
                <div className="rounded-md border p-4" ref={contentRef}>
                  {activePath ? (
                    content ? (
                      <div>
                        <Markdown>{content}</Markdown>
                      </div>
                    ) : <div className="text-sm text-muted-foreground">Loading…</div>
                  ) : (
                    <div className="text-sm text-muted-foreground">Select a document from the index or search.</div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
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


