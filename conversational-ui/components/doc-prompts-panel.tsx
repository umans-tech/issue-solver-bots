'use client';

import { useEffect, useMemo, useState } from 'react';
import useSWR from 'swr';
import { formatDistanceToNow } from 'date-fns';
import { ChevronDown, Loader2, Pencil, Trash2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Skeleton } from '@/components/ui/skeleton';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

interface DocPromptsResponse {
  knowledge_base_id: string;
  docs_prompts: Record<string, string>;
  updated_at?: string | null;
  last_process_id?: string | null;
  suggestions?: Record<string, { title: string; prompt: string }>;
}

interface DocPromptsPanelProps {
  knowledgeBaseId?: string | null;
  className?: string;
}

interface DraftEntry {
  id: string;
  slug: string;
  title: string;
  prompt: string;
  isEditing?: boolean;
}

const fetcher = async (url: string): Promise<DocPromptsResponse> => {
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail || body?.error || 'Failed to load prompts');
  }
  return res.json();
};

const slugify = (value: string) =>
  value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '') || 'doc';

const humanize = (slug: string) =>
  slug
    .split(/[-_]/g)
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(' ');
export function DocPromptsPanel({ knowledgeBaseId, className }: DocPromptsPanelProps) {
  const { data, error, isLoading, mutate } = useSWR<DocPromptsResponse>(
    knowledgeBaseId ? `/api/docs/prompts?knowledgeBaseId=${encodeURIComponent(knowledgeBaseId)}` : null,
    fetcher,
  );

  const savedEntries = useMemo<DraftEntry[]>(() => {
    const saved = data?.docs_prompts ?? {};
    return Object.entries(saved).map(([slug, prompt]) => ({
      id: slug,
      slug,
      title: humanize(slug),
      prompt,
    }));
  }, [data?.docs_prompts]);

  const savedKey = useMemo(() => JSON.stringify(savedEntries), [savedEntries]);
  const [drafts, setDrafts] = useState<DraftEntry[]>(savedEntries);
  const [isSaving, setIsSaving] = useState(false);
  const suggestions = data?.suggestions ?? {};

  useEffect(() => {
    setDrafts(savedEntries);
  }, [savedKey, savedEntries]);

  const updatedLabel = data?.updated_at
    ? formatDistanceToNow(new Date(data.updated_at), { addSuffix: true })
    : null;

  const hasChanges = savedKey !== JSON.stringify(drafts);

  const toggleEditor = (id: string, open: boolean) => {
    setDrafts((prev) => prev.map((entry) => (entry.id === id ? { ...entry, isEditing: open } : entry)));
  };

  const addCustomDoc = () => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    setDrafts((prev) => [
      ...prev,
      {
        id,
        slug: slugify('new-doc-' + Date.now()),
        title: 'New Doc',
        prompt: '',
        isEditing: true,
      },
    ]);
  };

  const insertSuggestion = (slug: string, prompt: string, title: string) => {
    setDrafts((prev) => [
      ...prev,
      {
        id: `${Date.now()}-${slug}`,
        slug,
        title,
        prompt,
        isEditing: true,
      },
    ]);
  };

  const handleDelete = (id: string) => {
    setDrafts((prev) => prev.filter((entry) => entry.id !== id));
  };

  const handleTitleChange = (id: string, title: string) => {
    const normalized = slugify(title);
    setDrafts((prev) =>
      prev.map((entry) =>
        entry.id === id ? { ...entry, title, slug: normalized || entry.slug } : entry,
      ),
    );
  };

  const handlePromptChange = (id: string, prompt: string) => {
    setDrafts((prev) => prev.map((entry) => (entry.id === id ? { ...entry, prompt } : entry)));
  };

  const handleSave = async () => {
    if (!knowledgeBaseId || !hasChanges) return;
    const payload: Record<string, string> = {};
    drafts.forEach((entry) => {
      payload[entry.slug] = entry.prompt.trim();
    });
    setIsSaving(true);
    try {
      const response = await fetch('/api/docs/prompts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ knowledgeBaseId, docsPrompts: payload }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body?.detail || body?.error || 'Unable to save prompts');
      }
      toast.success('Docs saved. They will be generated on the next sync.');
      await mutate();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Unable to save prompts');
    } finally {
      setIsSaving(false);
    }
  };

  if (!knowledgeBaseId) {
    return (
      <div className={cn('rounded-2xl border bg-card/60 p-4 shadow-sm text-sm text-muted-foreground', className)}>
        Connect a repository to configure automatic documentation.
      </div>
    );
  }

  return (
    <section className={cn('space-y-4', className)}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-foreground">Auto documentation</p>
          <p className="text-xs text-muted-foreground">Tell the agent what to write each sync.</p>
          {updatedLabel && <p className="text-[11px] text-muted-foreground/80 mt-1">Updated {updatedLabel}</p>}
        </div>
        <AddDocButton
          suggestions={suggestions}
          onAdd={addCustomDoc}
          onInsertSuggestion={insertSuggestion}
        />
      </div>
      {isLoading ? (
        <div className="space-y-2">
          {[0, 1, 2].map((key) => (
            <Skeleton key={key} className="h-16 w-full" />
          ))}
        </div>
      ) : error ? (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive">
          {error.message || 'Unable to load prompts'}
        </div>
      ) : drafts.length === 0 ? (
        <div className="rounded-md border border-dashed px-3 py-6 text-sm text-muted-foreground text-center">
          No docs selected. Use the arrow to pick a suggestion or add your own instructions.
        </div>
      ) : (
        <div className="space-y-2">
          {drafts.map((entry) => (
            <div key={entry.id} className="rounded-lg border px-3 py-2">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-medium text-foreground">{entry.title}</p>
                  <p className="text-[11px] text-muted-foreground">{entry.slug}</p>
                </div>
                <div className="flex gap-1">
                  <Button
                    type="button"
                    size="icon"
                    variant="ghost"
                    className="h-7 w-7"
                    onClick={() => toggleEditor(entry.id, !(entry.isEditing ?? false))}
                  >
                    <Pencil className="h-3.5 w-3.5" />
                    <span className="sr-only">Edit prompt</span>
                  </Button>
                  <Button type="button" size="icon" variant="ghost" className="h-7 w-7" onClick={() => handleDelete(entry.id)}>
                    <Trash2 className="h-3.5 w-3.5" />
                    <span className="sr-only">Remove prompt</span>
                  </Button>
                </div>
              </div>
              {entry.isEditing ? (
                <div className="mt-3 space-y-3">
                  <Input
                    value={entry.title}
                    onChange={(event) => handleTitleChange(entry.id, event.target.value)}
                    placeholder="Doc title"
                  />
                  <Textarea
                    value={entry.prompt}
                    onChange={(event) => handlePromptChange(entry.id, event.target.value)}
                    placeholder="Describe what this doc should contain"
                    rows={4}
                  />
                  <div className="flex justify-end">
                    <Button type="button" size="sm" variant="outline" onClick={() => toggleEditor(entry.id, false)}>
                      Done
                    </Button>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-muted-foreground mt-2 line-clamp-2">{entry.prompt}</p>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="flex items-center justify-end gap-2 border-t border-border/60 pt-3">
        <span className="mr-auto text-xs text-muted-foreground">
          {hasChanges ? 'Unsaved changes' : 'All changes saved'}
        </span>
        <Button type="button" variant="ghost" size="sm" disabled={!hasChanges || isSaving} onClick={() => setDrafts(savedEntries)}>
          Reset
        </Button>
        <Button type="button" size="sm" disabled={!hasChanges || isSaving} onClick={handleSave}>
          {isSaving ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Saving
            </>
          ) : (
            'Save docs'
          )}
        </Button>
      </div>
    </section>
  );
}
function AddDocButton({
  onAdd,
  suggestions,
  onInsertSuggestion,
}: {
  onAdd: () => void;
  suggestions: Record<string, { title: string; prompt: string }>;
  onInsertSuggestion: (slug: string, prompt: string, title: string) => void;
}) {
  const entries = Object.entries(suggestions);
  return (
    <div className="inline-flex rounded-md shadow-sm border border-input bg-background">
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={onAdd}
        className="rounded-r-none border-r border-border"
      >
        + Add doc
      </Button>
      {entries.length > 0 && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button type="button" variant="ghost" size="sm" className="rounded-l-none px-2">
              <ChevronDown className="h-3.5 w-3.5" />
              <span className="sr-only">Insert suggested prompt</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-72 max-h-80 overflow-y-auto">
            <DropdownMenuLabel className="text-xs text-muted-foreground uppercase tracking-wide">
              Pick a prompt
            </DropdownMenuLabel>
            {entries.map(([slug, meta]) => (
              <DropdownMenuItem
                key={slug}
                className="flex flex-col items-start gap-1 whitespace-normal"
                onSelect={() => onInsertSuggestion(slug, meta.prompt, meta.title)}
              >
                <span className="text-sm font-medium text-foreground">{meta.title}</span>
                <span className="text-xs text-muted-foreground leading-snug line-clamp-2">
                  {meta.prompt}
                </span>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      )}
    </div>
  );
}
