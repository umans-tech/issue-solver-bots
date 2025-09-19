const controllers = new Map<string, AbortController>();

export function setController(streamId: string, controller: AbortController) {
  controllers.set(streamId, controller);
}

export function getController(streamId: string) {
  return controllers.get(streamId) ?? null;
}

export function deleteController(streamId: string) {
  controllers.delete(streamId);
}

