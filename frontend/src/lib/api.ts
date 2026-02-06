import type { ApiError, ApiResponse } from './types';

const BASE_URL = '/api';

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = BASE_URL + endpoint;
  const config: RequestInit = {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    let detail: string | undefined;
    try {
      const body = (await response.json()) as Record<string, unknown>;
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body);
    } catch {
      detail = await response.text().catch(() => undefined);
    }
    throw {
      message: `HTTP ${response.status}: ${response.statusText}`,
      status: response.status,
      detail,
    } satisfies ApiError;
  }

  const ct = response.headers.get('content-type');
  if (ct && ct.includes('application/json')) {
    return response.json() as Promise<T>;
  }
  return response.text() as unknown as T;
}

export const api = {
  get: <T>(endpoint: string) => apiRequest<T>(endpoint, { method: 'GET' }),
  post: <T>(endpoint: string, body?: unknown) =>
    apiRequest<T>(endpoint, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    }),
  put: <T>(endpoint: string, body?: unknown) =>
    apiRequest<T>(endpoint, {
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    }),
  patch: <T>(endpoint: string, body?: unknown) =>
    apiRequest<T>(endpoint, {
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    }),
  del: <T>(endpoint: string) => apiRequest<T>(endpoint, { method: 'DELETE' }),
};

export function isApiError(error: unknown): error is ApiError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'message' in error &&
    'status' in error
  );
}

export async function fetchWithErrorHandling<T>(
  promise: Promise<T>
): Promise<ApiResponse<T>> {
  try {
    const data = await promise;
    return { data, success: true };
  } catch (error) {
    const message = isApiError(error)
      ? error.message
      : 'An unexpected error occurred';
    return { data: undefined as unknown as T, success: false, message };
  }
}
