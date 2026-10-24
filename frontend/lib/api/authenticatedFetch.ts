import { useAuthStore } from "../auth/store";

/** Use the current session at request time; never put credentials in URLs. */
export async function authenticatedFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const headers = new Headers(options.headers);
  const token = useAuthStore.getState().token;
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(url, { ...options, headers });
  // An old request must not clear a newer session established while it was in flight.
  if (response.status === 401 && token && useAuthStore.getState().token === token) {
    useAuthStore.setState({ token: null, user: null, isAuthenticated: false });
  }
  return response;
}
