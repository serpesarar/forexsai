import { useAuthStore } from "../auth/store";

/** Use the current session at request time; never put credentials in URLs. */
export function authenticatedFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const headers = new Headers(options.headers);
  const token = useAuthStore.getState().token;
  if (token) headers.set("Authorization", `Bearer ${token}`);
  return fetch(url, { ...options, headers });
}
