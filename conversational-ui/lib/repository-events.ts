export type RepositoryIndexedSummary = {
  sha: string;
  indexedAt?: string;
  branch?: string;
};

type EventLike = {
  type?: string | null;
  commit_sha?: string | null;
  occurred_at?: string | null;
  branch?: string | null;
};

export function extractRepositoryIndexedEvents(
  events: EventLike[] | undefined | null,
): RepositoryIndexedSummary[] {
  if (!Array.isArray(events)) return [];

  const summaries = events
    .filter((event) => {
      if (!event || typeof event.type !== 'string') return false;
      if (!event.commit_sha) return false;
      return event.type.toLowerCase() === 'repository_indexed';
    })
    .map((event) => ({
      sha: event.commit_sha as string,
      indexedAt: event.occurred_at ?? undefined,
      branch: event.branch ?? undefined,
    }))
    .sort((a, b) => {
      const aTime = a.indexedAt ? new Date(a.indexedAt).getTime() : 0;
      const bTime = b.indexedAt ? new Date(b.indexedAt).getTime() : 0;
      return aTime - bTime;
    });

  const seen = new Set<string>();
  const deduped: RepositoryIndexedSummary[] = [];
  for (let i = summaries.length - 1; i >= 0; i -= 1) {
    const entry = summaries[i];
    if (seen.has(entry.sha)) continue;
    seen.add(entry.sha);
    deduped.push(entry);
  }

  return deduped.reverse();
}
