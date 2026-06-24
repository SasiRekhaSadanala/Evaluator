// frontend/lib/api.ts
// Single source of truth for API base URL.
// All fetch calls in the project import from here.

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

/**
 * Authenticated fetch wrapper.
 * Usage: apiFetch("/api/evaluate", { method: "POST", body: formData })
 */
export async function apiFetch(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = typeof window !== "undefined"
    ? localStorage.getItem("auth_token")
    : null;

  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  // Only add Authorization if token exists
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Don't set Content-Type for FormData — browser sets it with boundary
  const isFormData = options.body instanceof FormData;
  if (!isFormData && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  return fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
}
