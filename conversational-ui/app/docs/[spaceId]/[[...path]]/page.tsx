"use client";

import { useCallback, useEffect, useMemo, useRef, useState, useTransition, type ReactNode } from 'react';
import {ChevronDown, Copy, Download, FileText, Settings, Sparkles, Activity, MoreVertical, RotateCcw, Wand2, ShieldCheck, ShieldOff} from 'lucide-react';
import { SharedHeader } from '@/components/shared-header';
import { Markdown } from '@/components/markdown';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { SearchIcon, CopyIcon } from '@/components/icons';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useSession } from 'next-auth/react';
import { useRouter, useParams, useSearchParams } from 'next/navigation';
import { Input } from '@/components/ui/input';
import { DocPromptsPanel } from '@/components/doc-prompts-panel';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import {Tooltip, TooltipContent, TooltipTrigger} from "@/components/ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { toast } from 'sonner';

type DocFileEntry = {
  path: string;
  title: string;
  origin?: string;
  process_id?: string;
  approved_by_id?: string;
  approved_by_name?: string;
  approved_at?: string;
};

type DocListEntry = {
  path: string;
  origin?: string;
  process_id?: string;
  approved_by_id?: string;
  approved_by_name?: string;
  approved_at?: string;
};

type DocFolderNode = {
  id: string;
  name: string;
  label: string;
  children: DocFolderNode[];
  files: DocFileEntry[];
};


export default function DocsPage() {
  const { data: session } = useSession();
  const router = useRouter();
  const params = useParams<{ spaceId: string; path?: string[] }>();
  const searchParams = useSearchParams();
  const rawSpaceId = typeof params?.spaceId === 'string' ? params.spaceId : '';
  const spaceId = rawSpaceId ? decodeURIComponent(rawSpaceId) : '';
  const sessionSpaceKbId = session?.user?.selectedSpace?.knowledgeBaseId || '';
  const kbId = spaceId || session?.user?.selectedSpace?.knowledgeBaseId;
  // commit sha is not currently typed on selectedSpace; leave undefined and rely on versions API
  const currentCommit = undefined as string | undefined;

  const [commitSha, setCommitSha] = useState<string | undefined>(currentCommit);
  const [versions, setVersions] = useState<string[]>([]);
  const [, setIndexMd] = useState<string>('');
  const [fileList, setFileList] = useState<DocListEntry[]>([]);
  const [isIndexLoading, setIsIndexLoading] = useState(false);
  const [titleMap, setTitleMap] = useState<Record<string, string>>({});
  const [activePath, setActivePathState] = useState<string | null>(null);
  const [activeProcessId, setActiveProcessId] = useState<string | null>(null);
  const [activeOrigin, setActiveOrigin] = useState<string | null>(null);
  const [content, setContent] = useState<string>('');
  const [contentStatus, setContentStatus] = useState<'idle' | 'loading' | 'ready' | 'missing'>('idle');
  const [versionsLoading, setVersionsLoading] = useState(true);
  const [q, setQ] = useState('');
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<{ path: string; snippet: string; line?: number; occurrence?: number; offset?: number }[]>([]);
  const [selectedIdx, setSelectedIdx] = useState<number>(0);
  const [, startTransition] = useTransition();
  const contentRef = useRef<HTMLDivElement | null>(null);
  const [toc, setToc] = useState<{ id: string; text: string; level: number }[]>([]);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const searchInputRef = useRef<HTMLInputElement | null>(null);
  const resultsContainerRef = useRef<HTMLDivElement | null>(null);
  const highlightTermRef = useRef<{ term: string; occurrence?: number } | null>(null);
  const lastCommitRef = useRef<string | undefined>(commitSha);
  const contentCacheRef = useRef<Map<string, string>>(new Map());
  const pendingFetchesRef = useRef<Map<string, Promise<string | null>>>(new Map());
  const [isAutoDocOpen, setIsAutoDocOpen] = useState(false);
  const openAutoDocSettings = useCallback(() => setIsAutoDocOpen(true), []);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [activeApproval, setActiveApproval] = useState<{ approved_by_id?: string; approved_by_name?: string; approved_at?: string } | null>(null);
  const promptIdForActiveDoc = useMemo(() => {
    if (!activePath) return null;
    const segments = activePath.split('/').filter(Boolean);
    const last = segments[segments.length - 1];
    return last ?? null;
  }, [activePath]);
  const pathSegments = Array.isArray(params?.path) ? params.path : [];
  const pathParam = pathSegments.length > 0 ? pathSegments.map(segment => decodeURIComponent(segment)).join('/') : null;
  const versionParam = searchParams?.get('v')?.trim() ?? null;
  const normalizedVersionParam = versionParam ? versionParam.toLowerCase() : null;
  const getCacheKey = useCallback((commit: string | undefined, pathValue: string | null) => (commit && pathValue ? `${commit}:${pathValue}` : null), []);
  const shortCommit = useMemo(() => (commitSha ? commitSha.slice(0, 7) : null), [commitSha]);
  const downloadFileName = useMemo(() => {
    if (!activePath) return 'document.md';
    const segments = activePath.split('/').filter((segment) => segment.length > 0);
    const lastSegment = segments[segments.length - 1] ?? 'document';
    return /\.md$/i.test(lastSegment) ? lastSegment : `${lastSegment}.md`;
  }, [activePath]);
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

  useEffect(() => {
    if (!sessionSpaceKbId) return;
    if (spaceId === sessionSpaceKbId) return;
    const destination = `/docs/${encodeURIComponent(sessionSpaceKbId)}`;
    router.replace(destination, { scroll: false });
  }, [router, spaceId, sessionSpaceKbId]);

  const encodePath = useCallback((value: string) => value.split('/').map(segment => encodeURIComponent(segment)).join('/'), []);

  const setActivePath = useCallback((next: string | null, options?: { replace?: boolean; versionOverride?: string | null }) => {
    setActivePathState(prev => (prev === next ? prev : next));
    const encodedSpace = spaceId ? encodeURIComponent(spaceId) : '';
    const baseRoot = encodedSpace ? `/docs/${encodedSpace}` : '/docs';
    const nextPath = next ? `${baseRoot}/${encodePath(next)}` : baseRoot;
    const versionToken = options?.versionOverride ?? shortCommit;
    const url = versionToken ? `${nextPath}?v=${encodeURIComponent(versionToken)}` : nextPath;
    if (options?.replace) {
      router.replace(url, { scroll: false });
    } else {
      router.push(url, { scroll: false });
    }
    if (typeof window !== 'undefined') {
      window.history.replaceState(null, '', url);
    }
  }, [router, encodePath, shortCommit, spaceId]);

  const fetchDoc = useCallback((pathValue: string) => {
    if (!kbId || !commitSha) return Promise.resolve<string | null>(null);
    const key = getCacheKey(commitSha, pathValue);
    if (!key) return Promise.resolve<string | null>(null);
    if (contentCacheRef.current.has(key)) {
      return Promise.resolve(contentCacheRef.current.get(key) ?? '');
    }
    const existing = pendingFetchesRef.current.get(key);
    if (existing) {
      return existing;
    }
    const request = (async () => {
      try {
        const res = await fetch(`/api/docs/file?kbId=${encodeURIComponent(kbId)}&commitSha=${encodeURIComponent(commitSha)}&path=${encodeURIComponent(pathValue)}`, { cache: 'no-store' });
        if (!res.ok) {
          return null;
        }
        const data = await res.json();
        const nextContent = typeof data?.content === 'string' ? data.content : '';
        contentCacheRef.current.set(key, nextContent);
        return nextContent;
      } catch {
        return null;
      } finally {
        pendingFetchesRef.current.delete(key);
      }
    })();
    pendingFetchesRef.current.set(key, request);
    return request;
  }, [commitSha, getCacheKey, kbId]);

  const prefetchDoc = useCallback((pathValue: string | null) => {
    if (!pathValue) return;
    void fetchDoc(pathValue);
  }, [fetchDoc]);

  useEffect(() => {
    contentCacheRef.current.clear();
    pendingFetchesRef.current.clear();
  }, [commitSha, kbId]);

  const navigateToPath = useCallback((next: string | null, options?: { replace?: boolean; versionOverride?: string | null }) => {
    startTransition(() => {
      setActivePath(next, options);
    });
  }, [setActivePath, startTransition]);

  const triggerManualAutoDoc = useCallback(
    async (mode: 'update' | 'complete') => {
      if (!kbId || !promptIdForActiveDoc) return;
      try {
        setIsGenerating(true);
        const res = await fetch('/api/docs/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            knowledgeBaseId: kbId,
            promptId: promptIdForActiveDoc,
            mode,
          }),
        });
        const payload = await res.json();
        if (!res.ok) {
          throw new Error(payload?.detail || payload?.error || 'Failed to trigger generation');
        }
        const processId = payload?.process_id;
        toast.success('Doc generation started', {
          description: processId ? (
            <>
              See progress{' '}
              <a
                href={`/tasks/${processId}`}
                target="_blank"
                rel="noreferrer"
                className="underline font-medium"
              >
                here
              </a>
              .
            </>
          ) : null,
          duration: 3500,
        });
      } catch (err) {
        toast.error(err instanceof Error ? err.message : 'Failed to start auto-doc');
      } finally {
        setIsGenerating(false);
      }
    },
    [kbId, promptIdForActiveDoc, toast],
  );

  const toggleApproval = useCallback(
    async (action: 'approve' | 'revoke') => {
      if (!kbId || !commitSha || !activePath) return;
      setIsApproving(true);
      try {
        const res = await fetch('/api/docs/approve', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ kbId, commitSha, path: activePath, action }),
        });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data?.error || 'Failed to update approval');
        }
        const meta = data?.metadata || {};
        setFileList((prev) => prev.map((entry) => {
          if (entry.path !== activePath) return entry;
          if (action === 'revoke') {
            const { approved_by_id, approved_by_name, approved_at, ...rest } = entry;
            return { ...rest } as DocFileEntry;
          }
          return { ...entry, ...meta } as DocFileEntry;
        }));
        if (action === 'revoke') {
          setActiveApproval(null);
        } else {
          setActiveApproval({
            approved_by_id: meta.approved_by_id,
            approved_by_name: meta.approved_by_name,
            approved_at: meta.approved_at,
          });
        }
        toast.success(action === 'approve' ? 'Document approved' : 'Approval revoked');
      } catch (err) {
        toast.error(err instanceof Error ? err.message : 'Failed to update approval');
      } finally {
        setIsApproving(false);
      }
    },
    [kbId, commitSha, activePath, toast],
  );


  const docTree = useMemo(() => {
    const formatSegment = (segment: string) => segment
      .replace(/[-_]+/g, ' ')
      .replace(/\b\w/g, (char) => char.toUpperCase());

    const root: DocFolderNode = { id: '', name: '', label: '', children: [], files: [] };

    const ensureChild = (parent: DocFolderNode, segment: string): DocFolderNode => {
      let child = parent.children.find((node) => node.name === segment);
      if (!child) {
        const id = parent.id ? `${parent.id}/${segment}` : segment;
        child = {
          id,
          name: segment,
          label: formatSegment(segment),
          children: [],
          files: [],
        };
        parent.children.push(child);
      }
      return child;
    };

    for (const entry of fileList) {
      const { path, origin, process_id } = entry;
      const parts = path.split('/').filter(Boolean);
      if (parts.length === 0) continue;
      let cursor = root;
      parts.forEach((segment, index) => {
        const isFile = index === parts.length - 1;
        if (isFile) {
          cursor.files.push({ path, title: titleMap[path] || segment, origin, process_id });
          return;
        }
        cursor = ensureChild(cursor, segment);
      });
    }

    const sortNode = (node: DocFolderNode) => {
      node.children.sort((a, b) => a.label.localeCompare(b.label, undefined, { sensitivity: 'base' }));
      node.children.forEach(sortNode);
      node.files.sort((a, b) => {
        const aName = a.path.split('/').pop() ?? a.path;
        const bName = b.path.split('/').pop() ?? b.path;
        const aIsIndex = aName.toLowerCase() === 'index.md';
        const bIsIndex = bName.toLowerCase() === 'index.md';
        if (aIsIndex !== bIsIndex) {
          return aIsIndex ? -1 : 1;
        }
        return a.title.localeCompare(b.title, undefined, { sensitivity: 'base' });
      });
    };

    sortNode(root);

    return root;
  }, [fileList, titleMap]);

  // Load versions on mount and pick commit based on URL query when possible
  useEffect(() => {
    if (!kbId) {
      setVersionsLoading(false);
      return;
    }

    const applyVersions = (available: string[]) => {
      setVersions(available);
      const matchedFromQuery = normalizedVersionParam
        ? available.find((sha: string) => sha.toLowerCase().startsWith(normalizedVersionParam))
        : undefined;
      setCommitSha((prev) => {
        if (matchedFromQuery) return matchedFromQuery;
        if (prev && available.includes(prev)) return prev;
        return available.length > 0 ? available[available.length - 1] : undefined;
      });
    };

    setVersionsLoading(true);
    (async () => {
      try {
        const res = await fetch(`/api/docs/versions?kbId=${encodeURIComponent(kbId)}`, { cache: 'no-store' });
        const data = await res.json();
        if (Array.isArray(data.versions)) {
          applyVersions(data.versions);
        }
      } catch {}
      setVersionsLoading(false);
    })();
  }, [kbId, normalizedVersionParam]);

  // Load index.md and files list
  useEffect(() => {
    if (!kbId || !commitSha) {
      setIsIndexLoading(false);
      return;
    }
    let cancelled = false;
    setIsIndexLoading(true);
    (async () => {
      try {
        const idx = await fetch(`/api/docs/index?kbId=${encodeURIComponent(kbId)}&commitSha=${encodeURIComponent(commitSha)}`, { cache: 'no-store' });
        const idxJson = await idx.json();
        if (!cancelled) {
          setIndexMd(idxJson?.content || '');
        }
      } catch {
        if (!cancelled) {
          setIndexMd('');
        }
      }
      try {
        const r = await fetch(`/api/docs/list?kbId=${encodeURIComponent(kbId)}&commitSha=${encodeURIComponent(commitSha)}`, { cache: 'no-store' });
        const j = await r.json();
        const files = Array.isArray(j.files) ? j.files : [];
        const metadataMap: Record<string, { origin?: string; process_id?: string; approved_by_id?: string; approved_by_name?: string; approved_at?: string }> = j.metadata && typeof j.metadata === 'object' ? j.metadata : {};
        if (!cancelled) {
          setFileList(files.map((path: string) => ({ 
            path, 
            origin: metadataMap[path]?.origin,
            process_id: metadataMap[path]?.process_id,
            approved_by_id: metadataMap[path]?.approved_by_id,
            approved_by_name: metadataMap[path]?.approved_by_name,
            approved_at: metadataMap[path]?.approved_at,
          })));
        }
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
        if (!cancelled) {
          const map: Record<string, string> = {};
          for (const [k, v] of entries) map[k] = v;
          setTitleMap(map);
        }
      } catch {
        if (!cancelled) {
          setFileList([]);
        }
      } finally {
        if (!cancelled) {
          setIsIndexLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [kbId, commitSha]);

  // Update activeProcessId and activeOrigin when activePath changes
  useEffect(() => {
    if (!activePath) {
      setActiveProcessId(null);
      setActiveOrigin(null);
      setActiveApproval(null);
      return;
    }
    const entry = fileList.find(f => f.path === activePath);
    setActiveProcessId(entry?.process_id ?? null);
    setActiveOrigin(entry?.origin ?? null);
    setActiveApproval(entry ? {
      approved_by_id: entry.approved_by_id,
      approved_by_name: entry.approved_by_name,
      approved_at: entry.approved_at,
    } : null);
  }, [activePath, fileList]);

  useEffect(() => {
    if (!kbId || !commitSha) return;
    if (!activePath) {
      setContent('');
      setContentStatus('idle');
      return;
    }
    const cacheKey = getCacheKey(commitSha, activePath);
    if (cacheKey) {
      const cached = contentCacheRef.current.get(cacheKey);
      if (cached !== undefined) {
        setContent(cached);
        setContentStatus('ready');
        return;
      }
    }
    setContentStatus('loading');
    let cancelled = false;
    fetchDoc(activePath).then((doc) => {
      if (cancelled) return;
      if (doc !== null) {
        setContent(doc);
        setContentStatus('ready');
      } else {
        setContent('');
        setContentStatus('missing');
      }
    });
    return () => {
      cancelled = true;
    };
  }, [kbId, commitSha, activePath, fetchDoc, getCacheKey]);

  useEffect(() => {
    if (lastCommitRef.current === commitSha) return;
    lastCommitRef.current = commitSha;
    if (activePath) {
      prefetchDoc(activePath);
    }
    setActivePath(activePath, { replace: true });
  }, [activePath, commitSha, prefetchDoc, setActivePath]);

  useEffect(() => {
    if (pathParam) {
      prefetchDoc(pathParam);
      return;
    }
    if (fileList.length > 0) {
      prefetchDoc(fileList[0].path);
      navigateToPath(fileList[0].path, { replace: true });
    }
  }, [fileList, pathParam, navigateToPath, prefetchDoc]);

  const approvalSummary = useMemo(() => {
    if (!activeApproval?.approved_at || !activeApproval?.approved_by_name) return null;
    const date = new Date(activeApproval.approved_at);
    const isValid = !Number.isNaN(date.getTime());
    const when = isValid ? date.toLocaleString() : activeApproval.approved_at;
    return `${activeApproval.approved_by_name} • ${when}`;
  }, [activeApproval]);

  useEffect(() => {
    const container = contentRef.current;
    if (!container || !content) {
      setToc([]);
      return;
    }

    let rafId: number | null = null;
    let observer: MutationObserver | null = null;

    const buildTocFromDom = () => {
      const headingElements = Array.from(container.querySelectorAll<HTMLElement>('h1, h2, h3'));
      if (headingElements.length === 0) {
        return false;
      }
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

      if (typeof window !== 'undefined') {
        const hash = window.location.hash.slice(1);
        if (hash) {
          const attemptNavigate = (retries = 40) => {
            const target = document.getElementById(hash);
            if (target) {
              handleTocNavigate(hash);
              return;
            }
            if (retries > 0) {
              window.setTimeout(() => attemptNavigate(retries - 1), 50);
            }
          };
          attemptNavigate();
        }
      }

      const pendingHighlight = highlightTermRef.current;
      if (pendingHighlight?.term.trim()) {
        highlightTermRef.current = null;
        highlightInContent(pendingHighlight);
      }
      return true;
    };

    const initialBuilt = buildTocFromDom();

    if (!initialBuilt && typeof MutationObserver !== 'undefined') {
      observer = new MutationObserver(() => {
        if (rafId) {
          window.cancelAnimationFrame(rafId);
        }
        rafId = window.requestAnimationFrame(() => {
          if (buildTocFromDom() && observer) {
            observer.disconnect();
            observer = null;
          }
        });
      });

      observer.observe(container, { childList: true, subtree: true });
    }

    return () => {
      if (observer) {
        observer.disconnect();
      }
      if (rafId) {
        window.cancelAnimationFrame(rafId);
      }
    };
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
    prefetchDoc(normalized);
    navigateToPath(normalized);
    setResults([]);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [navigateToPath, prefetchDoc, setResults]);

  const handleCopyMarkdown = useCallback(async () => {
    if (!content) return;

    try {
      if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(content);
        return;
      }
    } catch {
      // Fallback to legacy copy path below.
    }

    if (typeof document === 'undefined') return;

    // Legacy execCommand fallback avoids the deprecated type by redefining the surface locally.
    type LegacyDocument = Document & {
      execCommand?: (commandId: string, showUI?: boolean, value?: string) => boolean;
    };

    const textarea = document.createElement('textarea');
    textarea.value = content;
    textarea.setAttribute('readonly', '');
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    try {
      (document as LegacyDocument).execCommand?.('copy');
    } catch {
      // Ignore failures; there is no further fallback.
    } finally {
      document.body.removeChild(textarea);
    }
  }, [content]);

  const handleDownloadMarkdown = useCallback(() => {
    if (!content) return;
    if (typeof document === 'undefined' || typeof window === 'undefined') return;

    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = downloadFileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, [content, downloadFileName]);


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
    prefetchDoc(path);
    navigateToPath(path);
    resetSearchState();
  }, [activePath, highlightInContent, navigateToPath, prefetchDoc, q, resetSearchState]);

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

  const handleTocNavigate = useCallback((id: string) => {
    const el = document.getElementById(id);
    if (!el) return;

    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    const isFocusable = 'focus' in el;
    if (isFocusable) {
      (el as HTMLElement).focus({ preventScroll: true });
    }
    if (typeof window !== 'undefined') {
      const encodedSpace = spaceId ? encodeURIComponent(spaceId) : '';
      const baseRoot = encodedSpace ? `/docs/${encodedSpace}` : '/docs';
      const docPath = activePath ? `${baseRoot}/${encodePath(activePath)}` : baseRoot;
      const versionToken = shortCommit ? `?v=${encodeURIComponent(shortCommit)}` : '';
      window.history.replaceState(null, '', `${docPath}${versionToken}#${id}`);
    }
  }, [activePath, encodePath, shortCommit, spaceId]);

  useEffect(() => {
    if (typeof document === 'undefined') return;

    const handleClick = (event: MouseEvent) => {
      if (event.defaultPrevented) return;
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;

      const target = event.target as HTMLElement | null;
      if (!target) return;

      const anchor = target.closest('a');
      if (!anchor) return;

      const container = contentRef.current;
      if (!container || !container.contains(anchor)) return;

      const href = anchor.getAttribute('href');
      if (!href) return;

      const anchorElement = anchor as HTMLAnchorElement;
      const anchorHash = anchorElement.hash || (href.startsWith('#') ? href : null);
      if (
        anchorHash &&
        typeof window !== 'undefined' &&
        (!anchorElement.origin || anchorElement.origin === window.location.origin)
      ) {
        const targetId = (() => {
          const raw = anchorHash.replace(/^#/, '');
          try {
            return decodeURIComponent(raw);
          } catch {
            return raw;
          }
        })();

        if (targetId) {
          const targetElement = document.getElementById(targetId);
          if (targetElement && contentRef.current?.contains(targetElement)) {
            event.preventDefault();
            handleTocNavigate(targetId);
            return;
          }
        }
      }

      if (href.startsWith('http') || href.startsWith('mailto:')) return;
      if (href.startsWith('#')) return;

      event.preventDefault();
      handleMarkdownLink(href);
    };

    document.addEventListener('click', handleClick, true);
    return () => document.removeEventListener('click', handleClick, true);
  }, [handleMarkdownLink, handleTocNavigate]);

  const previousKbIdRef = useRef<string | null | undefined>(kbId);
  useEffect(() => {
    if (!kbId || previousKbIdRef.current === kbId) {
      previousKbIdRef.current = kbId;
      return;
    }
    previousKbIdRef.current = kbId;
    setCommitSha(currentCommit);
    setVersions([]);
    setFileList([]);
    setTitleMap({});
    setActivePathState(null);
    setContent('');
    setContentStatus('idle');
    setResults([]);
    setToc([]);
    contentCacheRef.current.clear();
    pendingFetchesRef.current.clear();
  }, [kbId, currentCommit]);


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
  const showContent = contentStatus === 'ready' || (contentStatus === 'loading' && !!content);
  const showInlineLoader = contentStatus === 'loading' && !!content;
  const showContentActions = showContent && !!content;
  const isApproved = !!activeApproval?.approved_by_id;

  const displayedItems = hasSearchQuery
    ? results.map((r) => ({
      key: `${r.path}-${r.offset ?? r.occurrence ?? r.line ?? 0}`,
      path: r.path,
      title: titleMap[r.path] || r.path,
      snippet: r.snippet || r.path,
      occurrence: r.occurrence,
    }))
    : fileList.slice(0, 10).map(({ path, origin }) => ({
      key: path,
      path,
      title: titleMap[path] || path,
      snippet: origin === 'auto' ? 'Auto documentation' : path,
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

  const renderFileEntry = (entry: DocFileEntry) => (
    <button
      key={entry.path}
      className={`flex w-full flex-col rounded-md px-3 py-2 text-left transition-colors ${activePath === entry.path ? 'text-primary font-semibold' : 'text-muted-foreground hover:text-foreground'}`}
      onClick={() => handleMarkdownLink(entry.path)}
      onMouseEnter={() => prefetchDoc(entry.path)}
      onFocus={() => prefetchDoc(entry.path)}
    >
      <span className="text-sm leading-snug flex items-center gap-2">
        {entry.title}
        {entry.origin === 'auto' && (
          <span className="inline-flex items-center rounded-full bg-primary/10 px-2 py-[1px] text-[10px] font-semibold uppercase tracking-wide text-primary">
            Auto
          </span>
        )}
        {entry.approved_by_name && (
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-[1px] text-[10px] font-semibold uppercase tracking-wide text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-100">
                Approved
              </span>
            </TooltipTrigger>
            <TooltipContent side="right">
              {entry.approved_by_name}
              {entry.approved_at ? ` • ${new Date(entry.approved_at).toLocaleString()}` : ''}
            </TooltipContent>
          </Tooltip>
        )}
      </span>
      <span className="text-[11px] text-muted-foreground/70 leading-tight">{entry.path}</span>
    </button>
  );

  const renderFolder = (node: DocFolderNode): ReactNode => {
    const label = node.label || node.name;
    return (
      <details key={node.id} className="group space-y-1" open>
        <summary className="flex cursor-pointer items-center justify-between px-3 py-1 text-sm font-semibold text-foreground list-none">
          <span>{label}</span>
          <ChevronDown
            aria-hidden="true"
            className="docs-index-caret h-4 w-4 text-muted-foreground/60 transition-transform duration-200 group-open:rotate-180"
          />
        </summary>
        <div className="mt-1 space-y-1 pl-3">
          {node.files.map(renderFileEntry)}
          {node.children.map(renderFolder)}
        </div>
      </details>
    );
  };

  const hasDocs = docTree.files.length > 0 || docTree.children.length > 0;
  const showLoadingShell = versionsLoading || isIndexLoading;
  const showEmptyState = !showLoadingShell && (!commitSha || !hasDocs);
  const isContentLoading = contentStatus === 'loading';

  return (
    <div className="flex flex-col min-w-0 h-dvh bg-background">
        <SharedHeader rightExtra={
            <div className="hidden md:flex items-center gap-3">
                <Tooltip>
                    <TooltipTrigger asChild>
                        <Button type="button" variant="outline" size="sm" onClick={openAutoDocSettings} disabled={!kbId}>
                            <Settings className="h-4 w-4"/>
                        </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                        Docs setup
                    </TooltipContent>
                </Tooltip>
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
          <Button
            type="button"
            variant="outline"
            size="icon"
            className="md:hidden"
            onClick={openAutoDocSettings}
            disabled={!kbId}
          >
            <Sparkles className="h-4 w-4" />
            <span className="sr-only">Docs setup</span>
          </Button>
        </div>
      </SharedHeader>
      <div className="flex-1 overflow-auto">
        <div className="mx-auto w-full max-w-[1440px] px-4 sm:px-6 lg:px-8 py-6">
          {!kbId ? (
            <div className="border rounded-md p-6 text-center text-muted-foreground">No knowledge base configured for this space.</div>
          ) : showEmptyState ? (
            <div className="flex flex-col gap-6 lg:grid lg:grid-cols-[minmax(0,1fr)_minmax(0,260px)] lg:items-start">
              <Card className="border-dashed border-muted">
                <CardHeader className="flex flex-col items-center gap-2 text-center">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
                    <FileText className="h-6 w-6 text-muted-foreground" />
                  </div>
                  <CardTitle className="text-lg">No docs yet</CardTitle>
                  <CardDescription className="max-w-md">
                    Configure prompts now so the next sync knows which docs to write.
                  </CardDescription>
                  <Button type="button" className="mt-2" onClick={openAutoDocSettings}>
                    Generate docs
                  </Button>
                </CardHeader>
              </Card>
            </div>
          ) : (
            <div className="flex flex-col gap-6 lg:grid lg:grid-cols-[minmax(0,260px)_minmax(0,1fr)_minmax(0,220px)] lg:items-start">
              <aside className="lg:sticky lg:top-24 h-fit text-sm">
                <div className="docs-index max-h-[calc(100vh-10rem)] overflow-y-auto pr-1 pt-4 space-y-4">
                  {showLoadingShell ? (
                    <div className="space-y-3 px-3">
                      {[0, 1, 2, 3, 4].map((key) => (
                        <Skeleton key={key} className="h-4 w-full" />
                      ))}
                    </div>
                  ) : !hasDocs ? (
                    <div className="px-3 py-2 text-xs text-muted-foreground">No files found.</div>
                  ) : (
                    <>
                      {docTree.files.length > 0 && (
                        <div className="space-y-1">
                          {docTree.files.map(renderFileEntry)}
                        </div>
                      )}
                      {docTree.children.map(renderFolder)}
                    </>
                  )}
                </div>
              </aside>

               <main className="min-w-0 relative">
                 {(showInlineLoader || showContentActions) && (
                   <div className="absolute right-0 top-0 z-20 flex flex-col items-end gap-2">
                        {showInlineLoader && (
                          <div className="rounded-md bg-muted/70 px-2 py-1 text-xs text-muted-foreground shadow-sm">
                            Loading latest…
                          </div>
                        )}
                        {showContentActions && (
                          <div className="flex items-center gap-1 rounded-md border border-border/70 bg-background/95 p-1 shadow-sm dark:bg-background/90">
                            {activeOrigin === 'auto' && (
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button
                                    type="button"
                                    variant={isApproved ? 'secondary' : 'outline'}
                                    size="icon"
                                    className="h-8 w-8 text-muted-foreground"
                                    onClick={() => toggleApproval(isApproved ? 'revoke' : 'approve')}
                                    disabled={isApproving || !kbId || !commitSha}
                                    aria-label={isApproved ? 'Revoke approval' : 'Approve document'}
                                  >
                                    {isApproved ? <ShieldCheck className="h-4 w-4 text-green-600 dark:text-green-500" /> : <ShieldOff className="h-4 w-4" />}
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent side="bottom">
                                  {isApproved
                                    ? approvalSummary || 'Approved'
                                    : 'Add a human approval seal'}
                                </TooltipContent>
                              </Tooltip>
                            )}
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  type="button"
                                  variant="ghost"
                                  size="icon"
                                  className="h-8 w-8 text-muted-foreground"
                                  onClick={handleCopyMarkdown}
                                  aria-label="Copy markdown"
                                >
                                  <Copy className="h-4 w-4" />
                                  <span className="sr-only">Copy markdown</span>
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent side="bottom">Copy markdown</TooltipContent>
                            </Tooltip>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  type="button"
                                  variant="ghost"
                                  size="icon"
                                  className="h-8 w-8 text-muted-foreground"
                                  onClick={handleDownloadMarkdown}
                                  aria-label="Download markdown"
                                >
                                  <Download className="h-4 w-4" />
                                  <span className="sr-only">Download markdown</span>
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent side="bottom">Download markdown</TooltipContent>
                            </Tooltip>
                            {activeOrigin === 'auto' && (
                              <DropdownMenu>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <DropdownMenuTrigger asChild>
                                      <Button
                                        type="button"
                                        variant="ghost"
                                        size="icon"
                                        className="h-8 w-8 text-muted-foreground hover:text-foreground"
                                        aria-label="Auto docs actions"
                                      >
                                        <MoreVertical className="h-4 w-4" />
                                        <span className="sr-only">Auto docs actions</span>
                                      </Button>
                                    </DropdownMenuTrigger>
                                  </TooltipTrigger>
                                  <TooltipContent side="bottom">Auto-doc actions</TooltipContent>
                                </Tooltip>
                                <DropdownMenuContent align="end" sideOffset={4}>
                                  {activeProcessId && (
                                    <DropdownMenuItem
                                      className="gap-2 text-sm"
                                      onClick={() =>
                                        window.open(`/tasks/${activeProcessId}`, '_blank', 'noopener,noreferrer')
                                      }
                                    >
                                      <Activity className="h-4 w-4" />
                                      View generation details
                                    </DropdownMenuItem>
                                  )}
                                  <DropdownMenuItem
                                    className="gap-2 text-sm"
                                    onClick={() => triggerManualAutoDoc('complete')}
                                    disabled={!promptIdForActiveDoc || isGenerating}
                                  >
                                    <RotateCcw className="h-4 w-4" />
                                    Re-generate
                                  </DropdownMenuItem>
                                  <DropdownMenuItem
                                    className="gap-2 text-sm"
                                    onClick={() => triggerManualAutoDoc('update')}
                                    disabled={!promptIdForActiveDoc || isGenerating}
                                  >
                                    <Wand2 className="h-4 w-4" />
                                    Update existing doc
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                 <div className="mx-auto max-w-7xl px-2 sm:px-4 pt-4" ref={contentRef}>
                   {showLoadingShell ? (
                     <div className="space-y-4">
                       <Skeleton className="h-8 w-1/2" />
                       <Skeleton className="h-4 w-full" />
                       <Skeleton className="h-4 w-5/6" />
                       <Skeleton className="h-4 w-2/3" />
                       <Skeleton className="h-4 w-full" />
                       <Skeleton className="h-4 w-3/4" />
                     </div>
                   ) : activePath ? (
                     contentStatus === 'missing' ? (
                       <div className="rounded-md border border-dashed border-border/80 bg-muted/30 px-4 py-5 text-sm text-muted-foreground">
                         We couldn't find this document in the selected version. Try another version or pick a different doc.
                       </div>
                     ) : showContent ? (
                       <div className="max-w-none prose prose-neutral dark:prose-invert">
                         {isApproved && (
                           <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-100">
                             <ShieldCheck className="h-3.5 w-3.5" />
                             <span>{approvalSummary || 'Approved'}</span>
                           </div>
                         )}
                         <Markdown>{content}</Markdown>
                       </div>
                     ) : (
                       <div className="space-y-4">
                         <Skeleton className="h-8 w-1/2" />
                         <Skeleton className="h-4 w-full" />
                         <Skeleton className="h-4 w-5/6" />
                         <Skeleton className="h-4 w-2/3" />
                         <Skeleton className="h-4 w-full" />
                         <Skeleton className="h-4 w-3/4" />
                       </div>
                     )
                   ) : (
                     <div className="text-sm text-muted-foreground">Select a document from the index.</div>
                   )}
                 </div>
               </main>

              <aside className="hidden lg:block lg:sticky lg:top-24 h-fit text-xs">
                <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground/80">On this page</div>
                <div className="mt-3 max-h-[calc(100vh-10rem)] overflow-y-auto pr-1 space-y-[2px] pt-1">
                  {showLoadingShell || isContentLoading ? (
                    <div className="space-y-2">
                      <Skeleton className="h-3 w-24" />
                      <Skeleton className="h-3 w-20" />
                      <Skeleton className="h-3 w-28" />
                      <Skeleton className="h-3 w-16" />
                    </div>
                  ) : toc.length > 0 ? (
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
                      prefetchDoc(item.path);
                    }}
                    onFocus={() => prefetchDoc(item.path)}
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
                      : showLoadingShell
                        ? 'Loading docs…'
                        : fileList.length === 0
                          ? 'No documents available yet.'
                          : 'Start typing to search docs.'}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      <Sheet open={isAutoDocOpen} onOpenChange={setIsAutoDocOpen}>
        <SheetContent side="right" className="w-full sm:max-w-md overflow-y-auto">
          <SheetHeader>
            <SheetTitle className="sr-only">Docs setup</SheetTitle>
          </SheetHeader>
          <DocPromptsPanel knowledgeBaseId={kbId} className="py-6" />
        </SheetContent>
      </Sheet>
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
