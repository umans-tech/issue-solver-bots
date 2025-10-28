'use client';

import { SearchIcon, FileTextIcon, ListIcon } from 'lucide-react';
import { memo } from 'react';

interface NotionMCPAnimationProps {
  toolName: string;
  args?: Record<string, unknown>;
}

export const NotionMCPAnimation = memo(function NotionMCPAnimation({
  toolName,
  args,
}: NotionMCPAnimationProps) {
  const getIcon = () => {
    switch (toolName) {
      case 'notion_search':
        return <SearchIcon className="size-4" />;
      case 'notion_get_page':
        return <FileTextIcon className="size-4" />;
      case 'notion_get_block_children':
        return <ListIcon className="size-4" />;
      default:
        return <FileTextIcon className="size-4" />;
    }
  };

  const getLabel = () => {
    switch (toolName) {
      case 'notion_search':
        return `Searching Notion for "${(args?.query as string) || '...'}"`;
      case 'notion_get_page':
        return 'Reading Notion page...';
      case 'notion_get_block_children':
        return 'Loading page content...';
      default:
        return 'Accessing Notion...';
    }
  };

  return (
    <div className="flex items-center gap-2 text-sm text-muted-foreground">
      {getIcon()}
      <span className="animate-pulse">{getLabel()}</span>
    </div>
  );
});

export function isNotionMCPTool(toolName: string): boolean {
  return toolName.startsWith('notion_');
}

interface NotionMCPResultProps {
  toolName: string;
  result?: unknown;
}

export const NotionMCPResult = memo(function NotionMCPResult({
  toolName,
  result,
}: NotionMCPResultProps) {
  if (!result || typeof result !== 'object') {
    return null;
  }

  const resultObj = result as Record<string, unknown>;
  const meta = resultObj._meta as Record<string, unknown> | undefined;

  return (
    <div className="rounded-lg border bg-muted/50 p-3 text-sm">
      <div className="flex items-center gap-2 font-medium mb-2">
        <FileTextIcon className="size-4" />
        <span>Notion {toolName.replace('notion_', '').replace('_', ' ')}</span>
      </div>
      
      {toolName === 'notion_search' && meta?.results && Array.isArray(meta.results) ? (
        <div className="space-y-2">
          {(meta.results as Array<Record<string, unknown>>).slice(0, 5).map((item, idx) => (
            <div key={idx} className="text-xs">
              <div className="font-medium">{item.title as string || 'Untitled'}</div>
              <div className="text-muted-foreground">
                {item.object as string} • {new Date(item.last_edited_time as string).toLocaleDateString()}
              </div>
            </div>
          ))}
          {(meta.results as Array<unknown>).length > 5 && (
            <div className="text-xs text-muted-foreground">
              +{(meta.results as Array<unknown>).length - 5} more results
            </div>
          )}
        </div>
      ) : null}
      
      {(toolName === 'notion_get_page' || toolName === 'notion_get_block_children') && (
        <div className="text-xs text-muted-foreground">
          Retrieved successfully
        </div>
      )}
    </div>
  );
});

