# 7. Adopt Short-Lived Process Cache for Conversational UI

Date: 2025-09-26

## Status

Proposed

## Context

- Three server routes — `/api/processes/[processId]`, `/api/repo`, and `/api/docs/versions` — frequently trigger together when the repo dialog or docs page mounts, each needing the full CUDU process snapshot.
- The shared header’s `useProcessStatus` hook fires immediately, so those routes often issue near-simultaneous CUDU calls (same tab, multi-tab, or fast refresh).
- Snapshots can be large and include sensitive data that we do not want to copy wholesale into the NextAuth session.
- We still need session updates for lightweight data (status, indexed SHA list), but those updates occur asynchronously on the client and may lag the first server reads.

### Why the session alone is not enough

- Server routes run before any React hook updates the session, so they must fetch the raw snapshot at least once.
- Storing the full snapshot in the session would bloat and expose data meant only for backend use.
- Other consumers (background tasks, additional tabs) can hit the APIs directly without the React hook ever running; they still need a fresh snapshot but should not stampede the CUDU API.

## Decision

Use a tiny per-runtime cache to share the most recent process snapshot for a few seconds.

1. Keep `lib/process-cache.ts`, an in-memory map keyed by process ID with a 5 s TTL (tunable, chosen to comfortably cover 1–2 s request bursts).
2. The first request to any of the routes fetches from CUDU, stores the snapshot, and subsequent requests within the TTL reuse it.
3. Keep `lib/repository-events.ts` as the single place where we distil `repository_indexed` events into commit SHA, branch, and timestamp.
4. Let `useProcessStatus` continue to push derived fields (status, indexed SHAs) into the session so the docs page can render quickly, while still relying on the cache when the session is not yet hydrated.

## Consequences

- **Less duplicate traffic:** Back-to-back server calls share the same snapshot instead of hitting CUDU two or three times.
- **Faster docs UX:** Newly indexed SHAs are available immediately (from cache now, from the session soon after).
- **Controlled staleness:** Data can be up to ~5 s old, which is acceptable for UI polling while keeping failures from being hidden for long.
- **Per-instance scope:** Each Next.js runtime keeps its own cache; horizontally scaled instances may still duplicate work.

## Alternatives Considered

- **Client-only debouncing:** Would not help server routes or other clients, so the CUDU bursts would remain.
- **Next.js `cache()` / `unstable_cache` or `fetch` revalidation:** Great for longer-lived caching, but heavier than needed for a sub-5 s burst window and harder to invalidate precisely.
- **Shared store (Redis, etc.):** Adds operational cost and complexity we do not need yet; reconsider if we scale beyond a handful of instances.

## Risks & Mitigations

- **Stale cache entries:** Overwrite the cache on every successful fetch and rely on the short TTL; consider webhook-triggered invalidation later.
- **Cache never hit:** Log hit/miss metrics so we can confirm real-world benefit and adjust TTL if needed.
- **Memory growth:** Snapshots are short-lived; monitor if payload size or process volume grows.

## Follow-Up

1. Add lightweight logging or metrics for cache hit/miss counts and downstream call volume.
2. Explore webhook-driven invalidation if we need fresher failure reporting.
3. Revisit the caching strategy (or adopt a shared store) if Conversational UI gains more instances.

## References

- Implementation: `conversational-ui/lib/process-cache.ts`, `conversational-ui/lib/repository-events.ts`
- Consumers: `conversational-ui/app/api/processes/[processId]/route.ts`, `conversational-ui/app/api/repo/route.ts`, `conversational-ui/app/api/docs/versions/route.ts`, `conversational-ui/hooks/use-process-status.ts`
