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

function formatPropertyValue(value: unknown): string {
  if (value === null || value === undefined) return '-';
  if (Array.isArray(value)) return value.join(', ');
  if (typeof value === 'boolean') return value ? '✓' : '✗';
  return String(value);
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

      {toolName === 'notion_list_databases' && meta?.databases && Array.isArray(meta.databases) ? (
        <div className="space-y-2">
          {(meta.databases as Array<Record<string, unknown>>).slice(0, 5).map((db, idx) => (
            <div key={idx} className="text-xs border-l-2 border-muted pl-2">
              <div className="font-medium">{db.title as string || 'Untitled Database'}</div>
              <div className="text-muted-foreground text-[10px]">
                ID: {String(db.id).slice(0, 8)}... • Last edited: {new Date(db.last_edited_time as string).toLocaleDateString()}
              </div>
            </div>
          ))}
          {(meta.databases as Array<unknown>).length > 5 && (
            <div className="text-xs text-muted-foreground">
              +{(meta.databases as Array<unknown>).length - 5} more databases
            </div>
          )}
        </div>
      ) : null}

      {toolName === 'notion_get_database' && meta?.properties ? (
        <div className="space-y-1">
          <div className="text-xs font-medium mb-1">Schema:</div>
          {Object.entries(meta.properties as Record<string, { type: string }>).slice(0, 10).map(([propName, propConfig]) => (
            <div key={propName} className="text-xs flex justify-between">
              <span className="font-medium">{propName}</span>
              <span className="text-muted-foreground text-[10px] uppercase">{propConfig.type}</span>
            </div>
          ))}
          {Object.keys(meta.properties as Record<string, unknown>).length > 10 && (
            <div className="text-xs text-muted-foreground">
              +{Object.keys(meta.properties as Record<string, unknown>).length - 10} more properties
            </div>
          )}
        </div>
      ) : null}

      {toolName === 'notion_query_database' && meta?.results && Array.isArray(meta.results) ? (
        <div className="space-y-2">
          {(meta.results as Array<Record<string, unknown>>).slice(0, 5).map((entry, idx) => {
            const properties = entry.properties as Record<string, { type: string; value: unknown }>;
            const titleProp = Object.entries(properties).find(([_, prop]) => prop.type === 'title');
            const title = titleProp ? formatPropertyValue(titleProp[1].value) : 'Untitled';
            
            return (
              <div key={idx} className="text-xs border-l-2 border-muted pl-2">
                <div className="font-medium mb-1">{title}</div>
                <div className="space-y-0.5">
                  {Object.entries(properties)
                    .filter(([_, prop]) => prop.type !== 'title')
                    .slice(0, 3)
                    .map(([propName, propValue]) => (
                      <div key={propName} className="text-[10px] flex gap-2">
                        <span className="text-muted-foreground">{propName}:</span>
                        <span>{formatPropertyValue(propValue.value)}</span>
                      </div>
                    ))}
                </div>
              </div>
            );
          })}
          {(meta.results as Array<unknown>).length > 5 && (
            <div className="text-xs text-muted-foreground">
              +{(meta.results as Array<unknown>).length - 5} more entries
            </div>
          )}
        </div>
      ) : null}

      {toolName === 'notion_create_page' && meta?.page_id ? (
        <div className="space-y-1">
          <div className="text-xs">
            <span className="text-green-600 dark:text-green-400 font-medium">✓ Page created</span>
          </div>
          <div className="text-[10px] text-muted-foreground space-y-0.5">
            <div>ID: {String(meta.page_id).slice(0, 12)}...</div>
            {meta.url ? (
              <a 
                href={meta.url as string} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 dark:text-blue-400 hover:underline"
              >
                Open in Notion →
              </a>
            ) : null}
          </div>
        </div>
      ) : null}

      {toolName === 'notion_update_page' && meta?.page_id ? (
        <div className="space-y-1">
          <div className="text-xs">
            <span className="text-green-600 dark:text-green-400 font-medium">✓ Page updated</span>
          </div>
          <div className="text-[10px] text-muted-foreground space-y-0.5">
            <div>ID: {String(meta.page_id).slice(0, 12)}...</div>
            {meta.last_edited_time ? (
              <div>Updated: {new Date(meta.last_edited_time as string).toLocaleString()}</div>
            ) : null}
            {meta.url ? (
              <a 
                href={meta.url as string} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 dark:text-blue-400 hover:underline"
              >
                View page →
              </a>
            ) : null}
          </div>
        </div>
      ) : null}

      {toolName === 'notion_append_blocks' && meta?.block_count !== undefined ? (
        <div className="text-xs">
          <span className="text-green-600 dark:text-green-400 font-medium">
            ✓ Appended {meta.block_count as number} block{(meta.block_count as number) !== 1 ? 's' : ''}
          </span>
        </div>
      ) : null}
    </div>
  );
});

