'use client';

import { useCallback, useMemo, useState } from 'react';
import useSWR from 'swr';
import { formatDistanceToNow } from 'date-fns';
import { Plus, Pencil, Trash2, Loader2, AlertCircle } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

interface DocPromptsResponse {
  knowledge_base_id: string;
  docs_prompts: Record<string, string>;
  updated_at?: string | null;
  last_process_id?: string | null;
}

interface DocPromptsPanelProps {
  knowledgeBaseId?: string | null;
  className?: string;
  variant?: 'card' | 'flat';
}

interface EditorState {
  mode: 'create' | 'edit';
  key?: string;
  name: string;
  instructions: string;
}

const fetcher = async (url: string): Promise<DocPromptsResponse> => {
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail || body?.error || 'Failed to load prompts');
  }
  const data: DocPromptsResponse = await res.json();
  return data;
};

const slugifyName = (value: string) =>
  value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '') || 'doc';

const humanizeSlug = (slug: string) =>
  slug
    .split(/[-_]/g)
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(' ');

const diffPrompts = (
  previous: Record<string, string>,
  next: Record<string, string>,
): Record<string, string> => {
  const payload: Record<string, string> = {};
  for (const [key, value] of Object.entries(next)) {
    if (previous[key] !== value) {
      payload[key] = value;
    }
  }
  for (const key of Object.keys(previous)) {
    if (!(key in next)) {
      payload[key] = '';
    }
  }
  return payload;
};

export function DocPromptsPanel({ knowledgeBaseId, className, variant = 'card' }: DocPromptsPanelProps) {
  const { data, error, isLoading, mutate } = useSWR<DocPromptsResponse>(
    knowledgeBaseId ? `/api/docs/prompts?knowledgeBaseId=${encodeURIComponent(knowledgeBaseId)}` : null,
    fetcher,
  );

  const prompts = data?.docs_prompts ?? {};
  const [editor, setEditor] = useState<EditorState | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const entries = useMemo(() => Object.entries(prompts).sort(([a], [b]) => a.localeCompare(b)), [prompts]);
  const updatedLabel = data?.updated_at ? formatDistanceToNow(new Date(data.updated_at), { addSuffix: true }) : null;

  const ensureUniqueSlug = useCallback(
    (baseName: string, currentKey?: string) => {
      let slug = slugifyName(baseName);
      if (currentKey && slug === currentKey) {
        return slug;
      }
      let suffix = 2;
      while (prompts[slug] !== undefined && slug !== currentKey) {
        slug = `${slugifyName(baseName)}-${suffix}`;
        suffix += 1;
      }
      return slug;
    },
    [prompts],
  );

  const resetEditor = useCallback(() => {
    setEditor(null);
    setFormError(null);
  }, []);

  const persistChanges = useCallback(
    async (nextPrompts: Record<string, string>) => {
      if (!knowledgeBaseId) return;
      const payload = diffPrompts(prompts, nextPrompts);
      if (Object.keys(payload).length === 0) {
        resetEditor();
        return;
      }

      setIsSaving(true);
      setFormError(null);
      try {
        const response = await fetch('/api/docs/prompts', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ knowledgeBaseId, docsPrompts: payload }),
        });
        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          throw new Error(body?.detail || body?.error || 'Unable to save prompts');
        }
        resetEditor();
        await mutate();
      } catch (persistError) {
        setFormError(persistError instanceof Error ? persistError.message : 'Unable to save prompts');
      } finally {
        setIsSaving(false);
      }
    },
    [knowledgeBaseId, mutate, prompts, resetEditor],
  );

  const handleSave = useCallback(async () => {
    if (!editor) return;
    const name = editor.name.trim();
    const instructions = editor.instructions.trim();
    if (!name || !instructions) {
      setFormError('Give the doc a name and describe what should be generated.');
      return;
    }
    const slug = ensureUniqueSlug(name, editor.key);
    const nextPrompts = { ...prompts };
    if (editor.mode === 'edit' && editor.key && editor.key !== slug) {
      delete nextPrompts[editor.key];
    }
    nextPrompts[slug] = instructions;
    await persistChanges(nextPrompts);
  }, [editor, ensureUniqueSlug, persistChanges, prompts]);

  const handleDelete = useCallback(
    async (key: string) => {
      if (!knowledgeBaseId) return;
      const confirmed = window.confirm('Stop generating this doc?');
      if (!confirmed) return;
      const nextPrompts = { ...prompts };
      delete nextPrompts[key];
      await persistChanges(nextPrompts);
    },
    [knowledgeBaseId, persistChanges, prompts],
  );

  const startCreate = useCallback(() => {
    if (!knowledgeBaseId) return;
    setEditor({ mode: 'create', name: '', instructions: '' });
    setFormError(null);
  }, [knowledgeBaseId]);

  const startEdit = useCallback(
    (key: string, value: string) => {
      setEditor({ mode: 'edit', key, name: humanizeSlug(key), instructions: value });
      setFormError(null);
    },
    [],
  );

  const renderEditor = () => {
    if (!editor) return null;
    return (
      <div className="rounded-lg border bg-muted/30 p-3 space-y-3">
        <div>
          <label className="text-xs font-medium text-muted-foreground">Doc name</label>
          <Input
            value={editor.name}
            onChange={(event) => setEditor((prev) => prev && ({ ...prev, name: event.target.value }))}
            placeholder="e.g. Incident runbook"
            className="mt-1"
            autoFocus
          />
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground">What should this doc include?</label>
          <Textarea
            value={editor.instructions}
            onChange={(event) => setEditor((prev) => prev && ({ ...prev, instructions: event.target.value }))}
            placeholder="Mention the audience, key sections, and any files to reference."
            className="mt-1"
            rows={4}
          />
          <p className="mt-1 text-[11px] text-muted-foreground/80">
            We’ll turn the name into a file-safe identifier automatically.
          </p>
        </div>
        <div className="flex items-center justify-end gap-2">
          <Button type="button" variant="ghost" size="sm" onClick={resetEditor} disabled={isSaving}>
            Cancel
          </Button>
          <Button type="button" size="sm" onClick={handleSave} disabled={isSaving}>
            {isSaving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving
              </>
            ) : editor.mode === 'edit' ? (
              'Update doc'
            ) : (
              'Save doc'
            )}
          </Button>
        </div>
      </div>
    );
  };

  const renderBody = () => {
    if (!knowledgeBaseId) {
      return (
        <div className="rounded-lg border border-dashed px-3 py-4 text-sm text-muted-foreground">
          Connect a repository to unlock automated documentation. Prompts live alongside each space so teammates can tweak them.
        </div>
      );
    }
    if (isLoading) {
      return (
        <div className="space-y-3">
          {[0, 1, 2].map((key) => (
            <Skeleton key={key} className="h-14 w-full" />
          ))}
        </div>
      );
    }
    if (error) {
      return (
        <div className="flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          <AlertCircle className="mt-0.5 h-4 w-4" />
          <span>{error.message || 'Unable to load prompts'}</span>
        </div>
      );
    }
    if (entries.length === 0 && !editor) {
      return (
        <div className="rounded-lg border border-dashed px-3 py-4 text-sm text-muted-foreground">
          No recipes yet. Add one to tell the agent which docs matter most. They run the next time your repo is indexed.
        </div>
      );
    }

    return (
      <div className="space-y-3">
        {entries.map(([key, value]) => (
          <div key={key} className="rounded-lg border px-3 py-2">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-foreground">{humanizeSlug(key)}</p>
                <p className="text-xs text-muted-foreground mt-1">{value}</p>
              </div>
              <div className="flex shrink-0 gap-1">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={() => startEdit(key, value)}
                >
                  <Pencil className="h-3.5 w-3.5" />
                  <span className="sr-only">Edit prompt</span>
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={() => handleDelete(key)}
                  disabled={isSaving}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  <span className="sr-only">Remove prompt</span>
                </Button>
              </div>
            </div>
          </div>
        ))}
        {renderEditor()}
        {formError && (
          <div className="flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/5 px-3 py-2 text-xs text-destructive">
            <AlertCircle className="mt-0.5 h-4 w-4" />
            <span>{formError}</span>
          </div>
        )}
      </div>
    );
  };

  const containerClass =
    variant === 'flat'
      ? 'space-y-4'
      : 'rounded-2xl border bg-card/60 p-4 shadow-sm';

  return (
    <section className={cn(containerClass, className)}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-foreground">Auto documentation</p>
          <p className="text-xs text-muted-foreground">Tell the agent what to write each sync.</p>
          {updatedLabel && (
            <p className="text-[11px] text-muted-foreground/80 mt-1">Updated {updatedLabel}</p>
          )}
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={startCreate}
          disabled={!knowledgeBaseId || isSaving}
        >
          <Plus className="mr-1.5 h-3.5 w-3.5" />
          Add doc to generate
        </Button>
      </div>
      <div className="mt-4 space-y-4">
        {renderBody()}
      </div>
    </section>
  );
}
