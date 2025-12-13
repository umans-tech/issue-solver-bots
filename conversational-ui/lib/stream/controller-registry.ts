const controllers = new Map<string, { controller: AbortController; createdAt: number }>();
const CONTROLLER_TTL_MS = 5 * 60 * 1000;

export function setController(streamId: string, controller: AbortController) {
  controllers.set(streamId, { controller, createdAt: Date.now() });
}

export function getController(streamId: string) {
  const entry = controllers.get(streamId);
  return entry?.controller ?? null;
}

export function deleteController(streamId: string) {
  controllers.delete(streamId);
}

export function pruneStaleControllers() {
  const now = Date.now();
  for (const [streamId, entry] of Array.from(controllers.entries())) {
    if (now - entry.createdAt >= CONTROLLER_TTL_MS) {
      entry.controller.abort();
      controllers.delete(streamId);
    }
  }
}

