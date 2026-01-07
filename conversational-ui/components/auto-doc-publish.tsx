'use client';

import { ExternalLink } from 'lucide-react';

export function AutoDocPublishResult({
  result,
}: {
  result: {
    error?: string;
    path?: string;
    commitSha?: string;
    docUrl?: string;
  };
}) {
  if (!result) return null;

  if (result.error) {
    return (
      <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive">
        Auto-doc publish failed: {result.error}
      </div>
    );
  }

  return (
    <div className="rounded-lg border px-3 py-2 text-sm">
      <p className="font-medium">Auto doc published</p>
      {result.path && (
        <p className="text-xs text-muted-foreground">{result.path}</p>
      )}
      {result.commitSha && (
        <p className="text-[11px] text-muted-foreground/80">
          Version {result.commitSha.slice(0, 7)}
        </p>
      )}
      {result.docUrl && (
        <a
          href={result.docUrl}
          className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-foreground underline"
        >
          Open doc <ExternalLink className="h-3 w-3" />
        </a>
      )}
    </div>
  );
}
