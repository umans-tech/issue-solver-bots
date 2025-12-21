// TTL-based controller registry to prevent memory leaks
const MAX_CONTROLLERS = 1000; // Prevent unbounded growth
const CONTROLLER_TTL_MS = 5 * 60 * 1000; // 5 minutes
const CLEANUP_INTERVAL_MS = 60 * 1000; // 1 minute

interface ControllerEntry {
  controller: AbortController;
  timestamp: number;
}

const controllers = new Map<string, ControllerEntry>();

// Periodic cleanup task
let cleanupTimer: NodeJS.Timeout | null = null;

function startCleanupTask() {
  if (!cleanupTimer) {
    cleanupTimer = setInterval(() => {
      const now = Date.now();
      const toDelete: string[] = [];

      for (const [streamId, entry] of controllers.entries()) {
        if (now - entry.timestamp > CONTROLLER_TTL_MS) {
          toDelete.push(streamId);
        }
      }

      for (const streamId of toDelete) {
        controllers.delete(streamId);
      }

      if (toDelete.length > 0) {
        console.log(`[controller-registry] Cleaned up ${toDelete.length} expired controllers`);
      }
    }, CLEANUP_INTERVAL_MS);

    // Don't prevent process exit
    if (cleanupTimer.unref) {
      cleanupTimer.unref();
    }
  }
}

export function setController(streamId: string, controller: AbortController) {
  // Enforce max size limit
  if (controllers.size >= MAX_CONTROLLERS) {
    // Remove oldest entry
    const firstKey = controllers.keys().next().value;
    if (firstKey) {
      controllers.delete(firstKey);
    }
  }

  controllers.set(streamId, {
    controller,
    timestamp: Date.now(),
  });

  startCleanupTask();
}

export function getController(streamId: string) {
  const entry = controllers.get(streamId);
  return entry?.controller ?? null;
}

export function deleteController(streamId: string) {
  controllers.delete(streamId);
}
