const DEFAULT_API_BASE = "http://localhost:8000";
const DEFAULT_WS_BASE = "ws://localhost:8000";

function normalizeBaseUrl(value: string): string {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}

export const API_BASE = normalizeBaseUrl(
  import.meta.env.VITE_API_URL ?? DEFAULT_API_BASE,
);

export const WS_BASE = normalizeBaseUrl(
  import.meta.env.VITE_WS_URL ?? DEFAULT_WS_BASE,
);

export const API_KEY = import.meta.env.VITE_API_KEY as string | undefined;
