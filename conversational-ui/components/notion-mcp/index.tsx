'use client';

import { motion } from 'framer-motion';
import { SiNotion } from 'react-icons/si';

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

export const NotionMCPAnimation = ({
  toolName,
  args,
}: {
  toolName: string;
  args?: Record<string, unknown>;
}) => {
  const details = summarizeArgs(args);
  return (
    <motion.div
      initial={{ opacity: 0.4, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className="rounded-lg border bg-muted/40 p-4"
    >
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-md bg-black text-white">
          <SiNotion className="h-5 w-5" />
        </div>
        <div>
          <p className="text-sm font-medium">Running {prettifyToolName(toolName)}</p>
          <p className="text-xs text-muted-foreground">Connecting to Notion workspace…</p>
        </div>
      </div>
      {details.length > 0 && (
        <ul className="mt-3 space-y-1 text-xs text-muted-foreground">
          {details.map((item) => (
            <li key={`${item.primary}-${item.secondary}`} className="flex items-start gap-2">
              <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 animate-pulse rounded-full bg-muted-foreground/60" />
              <span>
                <strong className="font-medium">{item.primary}:</strong> {item.secondary}
              </span>
            </li>
          ))}
        </ul>
      )}
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

  return (
    <div className="rounded-lg border bg-card p-4 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-md bg-black text-white">
          <SiNotion className="h-5 w-5" />
        </div>
        <div>
          <p className="text-sm font-semibold">{prettifyToolName(toolName)}</p>
          <p className="text-xs text-muted-foreground">Notion MCP tool result</p>
        </div>
      </div>

      {details.length > 0 && (
        <div className="mt-3 space-y-1">
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
        <div className="mt-4 space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Results
          </p>
          <div className="space-y-2">
            {summary.items.map((item) => (
              <div
                key={`${item.primary}-${item.secondary}`}
                className="rounded-md border border-muted bg-muted/40 p-2"
              >
                <p className="text-sm font-medium">{item.primary}</p>
                {item.secondary && (
                  <p className="text-xs text-muted-foreground">{item.secondary}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      ) : summary.text ? (
        <p className="mt-4 text-sm text-muted-foreground">{summary.text}</p>
      ) : summary.json ? (
        <pre className="mt-4 max-h-48 overflow-auto rounded-md bg-muted/40 p-3 text-xs text-muted-foreground">
          {JSON.stringify(summary.json, null, 2)}
        </pre>
      ) : null}
    </div>
  );
};
