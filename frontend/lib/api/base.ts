const FALLBACK_API_BASE = "";
const DEVELOPMENT_API_BASE = "http://localhost:8000";
const ALLOW_CROSS_ORIGIN_API = process.env.NEXT_PUBLIC_ALLOW_CROSS_ORIGIN_API === "true";

const LOCAL_HOST_PATTERN = /^(localhost|127(?:\.[0-9]+){3}|0\.0\.0\.0)(:\d+)?(\/.*)?$/i;

function trimTrailingSlash(value: string): string {
  return value.replace(/\/+$/, "");
}

function shouldForceSameOrigin(apiBase: string): boolean {
  if (ALLOW_CROSS_ORIGIN_API || typeof window === "undefined") {
    return false;
  }

  const hostname = window.location.hostname;
  if (LOCAL_HOST_PATTERN.test(hostname)) {
    return false;
  }

  if (!/^https?:\/\//i.test(apiBase)) {
    return false;
  }

  try {
    return new URL(apiBase).origin !== window.location.origin;
  } catch {
    return false;
  }
}

export function normalizeApiBase(rawValue?: string | null): string {
  const candidate = (rawValue ?? "").trim();

  if (!candidate) {
    return FALLBACK_API_BASE;
  }

  if (/^https?:\/\//i.test(candidate)) {
    return trimTrailingSlash(candidate);
  }

  if (candidate.startsWith("//")) {
    return trimTrailingSlash(`https:${candidate}`);
  }

  if (candidate.startsWith("/")) {
    return trimTrailingSlash(candidate);
  }

  const sanitized = candidate.replace(/^\/+/, "");
  const protocol = LOCAL_HOST_PATTERN.test(sanitized) ? "http" : "https";
  return trimTrailingSlash(`${protocol}://${sanitized}`);
}

export function getApiBase(): string {
  if ((process.env.NEXT_PUBLIC_API_URL ?? "").trim()) {
    const normalizedBase = normalizeApiBase(process.env.NEXT_PUBLIC_API_URL);
    return shouldForceSameOrigin(normalizedBase) ? FALLBACK_API_BASE : normalizedBase;
  }

  if (process.env.NODE_ENV === "development") {
    return DEVELOPMENT_API_BASE;
  }

  return FALLBACK_API_BASE;
}

export function buildApiUrl(endpoint: string): string {
  const normalizedEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  return `${getApiBase()}${normalizedEndpoint}`;
}

export function buildWebSocketUrl(endpoint: string): string {
  const normalizedEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const apiBase = getApiBase();

  const absoluteBase = /^https?:\/\//i.test(apiBase)
    ? apiBase
    : typeof window !== "undefined"
      ? new URL(apiBase || "/", window.location.origin).toString().replace(/\/+$/, "")
      : "http://localhost:8000";

  const websocketBase = absoluteBase.replace(/\/api\/?$/, "").replace(/^http/i, "ws");
  return `${websocketBase}${normalizedEndpoint}`;
}