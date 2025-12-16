type ControllerEntry = {
  controller: AbortController;
  createdAt: number;
};

const controllers = new Map<string, ControllerEntry>();

// Evict controllers older than 10 minutes to prevent memory leaks
const MAX_CONTROLLER_AGE_MS = 10 * 60 * 1000;
const MAX_CONTROLLERS = 1000;

function evictStaleControllers() {
  const now = Date.now();
  const toDelete: string[] = [];

  // Convert to array for iteration compatibility
  const entries = Array.from(controllers.entries());
  for (const [streamId, entry] of entries) {
    if (now - entry.createdAt > MAX_CONTROLLER_AGE_MS) {
      toDelete.push(streamId);
      // Abort the controller if it's still active
      if (!entry.controller.signal.aborted) {
        entry.controller.abort('Controller evicted due to age');
      }
    }
  }

  toDelete.forEach((streamId) => controllers.delete(streamId));

  // If still too many controllers, evict oldest
  if (controllers.size > MAX_CONTROLLERS) {
    const sortedEntries = Array.from(controllers.entries()).sort(
      ([, a], [, b]) => a.createdAt - b.createdAt,
    );
    const excess = controllers.size - MAX_CONTROLLERS;
    for (let i = 0; i < excess; i++) {
      const [streamId, entry] = sortedEntries[i];
      if (!entry.controller.signal.aborted) {
        entry.controller.abort('Controller evicted due to capacity');
      }
      controllers.delete(streamId);
    }
  }
}

export function setController(streamId: string, controller: AbortController) {
  // Clean up stale controllers periodically
  if (controllers.size > 0 && Math.random() < 0.1) {
    evictStaleControllers();
  }

  controllers.set(streamId, {
    controller,
    createdAt: Date.now(),
  });
}

export function getController(streamId: string) {
  const entry = controllers.get(streamId);
  return entry?.controller ?? null;
}

export function deleteController(streamId: string) {
  const entry = controllers.get(streamId);
  if (entry && !entry.controller.signal.aborted) {
    // Abort controller before deletion if not already aborted
    entry.controller.abort('Stream completed or cancelled');
  }
  controllers.delete(streamId);
}

// Export for health monitoring
export function getControllerStats() {
  evictStaleControllers();
  return {
    total: controllers.size,
    active: Array.from(controllers.values()).filter(
      (e) => !e.controller.signal.aborted,
    ).length,
  };
}
