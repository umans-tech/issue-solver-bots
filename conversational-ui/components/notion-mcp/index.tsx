'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { SiNotion } from 'react-icons/si';
import { ChevronDown } from 'lucide-react';

type NotionSummaryItem = {
  primary: string;
  secondary?: string;
};

type NotionSummary = {
  items?: NotionSummaryItem[];
  text?: string;
  json?: unknown;
};

const HINT_PREFIXES = ['notion', 'page', 'database', 'workspace', 'block', 'search'];

export const isNotionMCPTool = (toolName: string): boolean => {
  const name = toolName.toLowerCase();
  return HINT_PREFIXES.some((hint) => name.startsWith(hint) || name.includes(`.${hint}`));
};

const prettifyToolName = (toolName: string): string =>
  toolName
    .replace(/^notion[._-]?/i, '')
    .replace(/[_-]/g, ' ')
    .replace(/\b([a-z])/g, (match) => match.toUpperCase());

const summarizeArgs = (args: any): NotionSummaryItem[] => {
  if (!args || typeof args !== 'object') return [];
  return Object.entries(args)
    .filter(([, value]) => value != null && value !== '')
    .slice(0, 3)
    .map(([key, value]) => ({
      primary: prettifyToolName(key),
      secondary: typeof value === 'string' ? value : JSON.stringify(value),
    }));
};

const summarizeResult = (result: any): NotionSummary => {
  if (!result) {
    return { text: 'No result returned.' };
  }

  const unwrap = (value: any) =>
    Array.isArray(value?.results)
      ? value.results
      : Array.isArray(value?.data)
        ? value.data
        : Array.isArray(value)
          ? value
          : null;

  const collection = unwrap(result);
  if (collection) {
    const items = collection.slice(0, 5).map((item: any) => {
      const title =
        item?.title?.plain_text ||
        item?.name ||
        item?.properties?.title?.plain_text ||
        item?.id ||
        'Untitled';
      const secondary = item?.url || item?.properties?.url || item?.created_time;
      return { primary: String(title), secondary: secondary ? String(secondary) : undefined };
    });
    return { items };
  }

  if (typeof result === 'string') {
    return { text: result };
  }

  if (typeof result === 'object') {
    return { json: result };
  }

  return { text: String(result) };
};

const truncate = (value?: string, max = 36) => {
  if (!value) return '';
  return value.length > max ? `${value.slice(0, max)}…` : value;
};

const getArg = (args: Record<string, unknown> | undefined, keys: string[]): string | undefined => {
  if (!args) return undefined;
  for (const key of keys) {
    const value = args[key];
    if (typeof value === 'string' && value.trim().length > 0) {
      return value.trim();
    }
  }
  return undefined;
};

const isLikelyId = (value?: string) => {
  if (!value) return false;
  const cleaned = value.replace(/[^a-z0-9]/gi, '');
  return cleaned.length >= 16 && /^[a-f0-9]+$/i.test(cleaned);
};

const findReadableString = (input: unknown, depth = 0): string | undefined => {
  if (typeof input === 'string') {
    const trimmed = input.trim();
    if (!trimmed || isLikelyId(trimmed)) return undefined;
    return trimmed;
  }
  if (!input || depth > 2) return undefined;
  if (Array.isArray(input)) {
    for (const item of input) {
      const result = findReadableString(item, depth + 1);
      if (result) return result;
    }
    return undefined;
  }
  if (typeof input === 'object') {
    for (const value of Object.values(input as Record<string, unknown>)) {
      const result = findReadableString(value, depth + 1);
      if (result) return result;
    }
  }
  return undefined;
};

const normalizeToolName = (toolName: string) => toolName.replace(/^notion[._-]?/i, '').toLowerCase();

const animationTextForTool = (rawToolName: string, args?: Record<string, unknown>): string => {
  const normalized = normalizeToolName(rawToolName);

  const formatQuoted = (value?: string, max = 36) => {
    if (!value) return undefined;
    const trimmed = value.trim();
    if (!trimmed || isLikelyId(trimmed)) return undefined;
    return `"${truncate(trimmed, max)}"`;
  };

  const extractQuery = () => formatQuoted(getArg(args, ['query', 'q', 'search']), 48);

  const extractTitle = () =>
    formatQuoted(
      getArg(args, ['title', 'name']) ||
        findReadableString(args && (args as any).title) ||
        findReadableString(args && (args as any).name),
      48,
    );

  const extractId = () => formatQuoted(getArg(args, ['id', 'page_id', 'pageId', 'database_id', 'databaseId']), 32);

  switch (normalized) {
    case 'search': {
      const query = extractQuery();
      return query ? `Searching Notion for ${query}...` : 'Searching across Notion...';
    }
    case 'fetch': {
      const target = extractTitle() || extractId();
      return target ? `Fetching Notion content ${target}...` : 'Fetching Notion content...';
    }
    case 'create-pages': {
      const title = extractTitle();
      return title ? `Creating Notion page ${title}...` : 'Creating a Notion page...';
    }
    case 'update-page': {
      const target = extractTitle() || extractId();
      return target ? `Updating Notion page ${target}...` : 'Updating a Notion page...';
    }
    case 'create-database':
      return 'Creating a Notion database...';
    case 'update-database':
      return 'Updating a Notion database...';
    case 'move-pages':
      return 'Moving Notion pages...';
    case 'duplicate-page':
      return 'Duplicating a Notion page...';
    case 'create-comment':
      return 'Adding a Notion comment...';
    case 'get-comments':
      return 'Retrieving Notion comments...';
    default: {
      const fallback = prettifyToolName(rawToolName);
      return `Running Notion tool: ${fallback}...`;
    }
  }
};

const resultSummaryText = (rawToolName: string, args?: Record<string, unknown>) => {
  const normalized = normalizeToolName(rawToolName);

  const quoted = (value?: string, max = 48) =>
    value && value.trim().length ? `"${truncate(value.trim(), max)}"` : undefined;

  const extractQuery = () => quoted(getArg(args, ['query', 'q', 'search']));
  const extractTitle = () =>
    quoted(
      getArg(args, ['title', 'name']) ||
        findReadableString(args && (args as any).title) ||
        findReadableString(args && (args as any).name),
    );
  const extractId = () => quoted(getArg(args, ['id', 'page_id', 'pageId', 'database_id', 'databaseId']), 32);

  switch (normalized) {
    case 'search': {
      const query = extractQuery();
      return query ? `Searched Notion for: ${query}` : 'Searched across Notion.';
    }
    case 'fetch': {
      const target = extractTitle() || extractId();
      return target ? `Fetched Notion content: ${target}` : 'Fetched Notion content.';
    }
    case 'create-pages': {
      const title = extractTitle();
      return title ? `Created Notion page: ${title}` : 'Created a Notion page.';
    }
    case 'update-page': {
      const target = extractTitle() || extractId();
      return target ? `Updated Notion page: ${target}` : 'Updated a Notion page.';
    }
    case 'create-database':
      return 'Created a Notion database.';
    case 'update-database':
      return 'Updated a Notion database.';
    case 'move-pages':
      return 'Moved Notion pages.';
    case 'duplicate-page':
      return 'Duplicated a Notion page.';
    case 'create-comment':
      return 'Added a Notion comment.';
    case 'get-comments':
      return 'Retrieved Notion comments.';
    default: {
      const text = animationTextForTool(rawToolName, args).replace(/\.\.\.$/, '');
      if (!text) return 'Completed Notion tool.';
      return `${text[0].toUpperCase()}${text.slice(1)}.`;
    }
  }
};

export const NotionMCPAnimation = ({
  toolName,
  args,
}: {
  toolName: string;
  args?: Record<string, unknown>;
}) => {
  const text = animationTextForTool(toolName, args);
  return (
    <motion.div
      initial={{ opacity: 0.6, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.2 }}
      className="flex items-center gap-2 text-sm text-muted-foreground"
    >
      <span className="flex h-6 w-6 items-center justify-center rounded-md bg-black text-white">
        <SiNotion className="h-4 w-4" />
      </span>
      <span className="truncate max-w-[320px] animate-pulse">{text}</span>
    </motion.div>
  );
};

export const NotionMCPResult = ({
  toolName,
  result,
  args,
}: {
  toolName: string;
  result: unknown;
  args?: Record<string, unknown>;
}) => {
  const summary = summarizeResult(result);
  const details = summarizeArgs(args);
  const [expanded, setExpanded] = useState(false);
  const summaryLine = resultSummaryText(toolName, args);

  return (
    <div className="flex flex-col gap-2">
      <div className="inline-flex max-w-full items-center gap-2 text-sm text-muted-foreground">
        <span className="flex h-6 w-6 items-center justify-center rounded-md bg-black text-white">
          <SiNotion className="h-4 w-4" />
        </span>
        <span
          className="flex cursor-pointer items-center gap-1 select-none hover:text-foreground"
          onClick={() => setExpanded((prev) => !prev)}
        >
          <span className="truncate max-w-[320px]">{summaryLine}</span>
          <ChevronDown
            className={`h-4 w-4 transition-transform ${expanded ? 'rotate-180' : ''}`}
          />
        </span>
      </div>

      {expanded && (
        <div className="space-y-3 rounded-md border border-border bg-card/60 p-4">
          {details.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Parameters</p>
              <ul className="text-xs text-muted-foreground">
                {details.map((item) => (
                  <li key={`${item.primary}-${item.secondary}`}>
                    <strong>{item.primary}:</strong> {item.secondary}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {summary.items && summary.items.length > 0 ? (
            <div className="space-y-2">
              {summary.items.map((item) => (
                <div
                  key={`${item.primary}-${item.secondary}`}
                  className="rounded-md border border-border/60 bg-background/80 px-3 py-2"
                >
                  <p className="text-sm font-medium text-foreground">{item.primary}</p>
                  {item.secondary && (
                    <p className="text-xs text-muted-foreground">{item.secondary}</p>
                  )}
                </div>
              ))}
            </div>
          ) : summary.text ? (
            <p className="text-sm text-muted-foreground">{summary.text}</p>
          ) : summary.json ? (
            <pre className="max-h-48 overflow-auto rounded-md bg-background/80 p-3 text-xs text-muted-foreground">
              {JSON.stringify(summary.json, null, 2)}
            </pre>
          ) : null}
        </div>
      )}
    </div>
  );
};
