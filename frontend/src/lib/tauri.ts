// Tauri API wrapper - provides safe access to Tauri APIs
// These functions are no-ops when running in a browser (non-Tauri environment)

declare global {
  interface Window {
    __TAURI_INTERNALS__?: Record<string, unknown>;
  }
}

/** Check if running inside Tauri desktop app */
export function isTauri(): boolean {
  return typeof window !== 'undefined' && !!window.__TAURI_INTERNALS__;
}

/** Invoke a Tauri command. Returns undefined if not in Tauri. */
export async function tauriInvoke<T = unknown>(
  cmd: string,
  args?: Record<string, unknown>
): Promise<T | undefined> {
  if (!isTauri()) return undefined;
  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const m = await (Function('return import("@tauri-apps/api/core")')() as Promise<any>);
    return m.invoke(cmd, args) as Promise<T>;
  } catch {
    return undefined;
  }
}

/** Listen for a Tauri event. Returns a cleanup function. */
export function tauriListen<T = unknown>(
  event: string,
  handler: (payload: T) => void
): () => void {
  if (!isTauri()) return () => {};

  let cleanup: (() => void) | undefined;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (Function('return import("@tauri-apps/api/event")')() as Promise<any>)
    .then((m) => {
      return m.listen(event, (e: { payload: T }) => handler(e.payload));
    })
    .then((fn: () => void) => {
      cleanup = fn;
    });

  return () => cleanup?.();
}

export {};
