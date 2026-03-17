/**
 * Shared API configuration for all service files.
 * Centralizes the API base URL and auth headers so every fetch call
 * goes through one place.
 */

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const API_AUTH_TOKEN = import.meta.env.VITE_API_AUTH_TOKEN || '';

/**
 * Returns headers with Content-Type and optional Bearer token.
 * When VITE_API_AUTH_TOKEN is not set (local dev), no auth header is sent.
 */
export function getAuthHeaders(contentType = 'application/json'): Record<string, string> {
  const headers: Record<string, string> = {};
  if (contentType) {
    headers['Content-Type'] = contentType;
  }
  if (API_AUTH_TOKEN) {
    headers['Authorization'] = `Bearer ${API_AUTH_TOKEN}`;
  }
  return headers;
}

/**
 * Returns only the auth header (no Content-Type), useful for GET requests
 * or requests where Content-Type is not needed.
 */
export function getAuthOnlyHeaders(): Record<string, string> {
  const headers: Record<string, string> = {};
  if (API_AUTH_TOKEN) {
    headers['Authorization'] = `Bearer ${API_AUTH_TOKEN}`;
  }
  return headers;
}
