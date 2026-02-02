/**
 * Single source of truth for backend API base URL.
 * Reads NEXT_PUBLIC_API_BASE_URL or NEXT_PUBLIC_API_URL (no hardcoded URLs).
 * For production (e.g. Render) set in dashboard; locally use .env.local.
 */
function getApiBaseUrl(): string {
  const raw =
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    'http://localhost:8000';
  const base = raw.replace(/\/$/, '');
  return base.includes('/api/v1') ? base : `${base}/api/v1`;
}

/** Auth headers for API requests (JWT from storage if present). */
function getAuthHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  return {
    ...extra,
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export { getApiBaseUrl, getAuthHeaders };

/**
 * Authenticated fetch to API (same base URL + JWT). Use for blob/download or custom responses.
 */
export async function apiFetch(endpoint: string, init: RequestInit = {}): Promise<Response> {
  const url = `${getApiBaseUrl()}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  const headers: Record<string, string> = {};
  if (init.headers) {
    if (init.headers instanceof Headers) {
      init.headers.forEach((value, key) => { headers[key] = value; });
    } else if (Array.isArray(init.headers)) {
      for (const [key, value] of init.headers) headers[key] = value;
    } else Object.assign(headers, init.headers as Record<string, string>);
  }
  Object.assign(headers, getAuthHeaders());
  return fetch(url, { ...init, headers, credentials: 'include' });
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const isFormData = options.body instanceof FormData;
  const headers: Record<string, string> = {};
  if (options.headers) {
    if (options.headers instanceof Headers) {
      options.headers.forEach((value, key) => { headers[key] = value; });
    } else if (Array.isArray(options.headers)) {
      for (const [key, value] of options.headers) {
        headers[key] = value;
      }
    } else {
      Object.assign(headers, options.headers);
    }
  }
  if (!isFormData) {
    headers['Content-Type'] = 'application/json';
  }
  Object.assign(headers, getAuthHeaders());

  try {
    const response = await fetch(`${getApiBaseUrl()}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`, {
        ...options,
        headers,
        credentials: 'include',  // FIXED: Include credentials for CORS
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        // For 409 conflicts, return the full error object with duplicate info
        if (response.status === 409) {
          // errorData might be the direct object or wrapped in detail
          const duplicateInfo = errorData.existing_person_id ? errorData : (errorData.detail || errorData);
          return { 
            error: JSON.stringify({
              status: 409,
              message: duplicateInfo.message || "Duplicate person found",
              existing_person_id: duplicateInfo.existing_person_id,
              existing_employee_code: duplicateInfo.existing_employee_code
            })
          };
        }
        return { error: errorData.detail || errorData.message || `HTTP error! status: ${response.status}` };
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'An unknown error occurred' };
    }
}

export const auth = {
  login: async (email: string, password: string) => {
    return apiRequest<{ access_token: string; user: any }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },
  me: async () => {
    return apiRequest<any>('/auth/me', {
      method: 'GET',
    });
  },
};

// Admin Person Viewer (Step-14): global read-only persons + document download
export interface AdminPersonListItem {
  id: string;
  name: string;
  email: string | null;
  employee_code: string | null;
  department_id: number | null;
  department_name: string | null;
  status: string | null;
  created_at: string | null;
}

export interface AdminPersonDocItem {
  id: number;
  filename: string;
  doc_name: string;
  doc_type: string | null;
  doc_category: string | null;
  stage: string | null;
  uploaded_at: string | null;
  uploaded_by_dept: string | null;
  expires_at: string | null;
  status: string;
  mime_type?: string;
  size_bytes?: number;
}

export const admin = {
  listPersons: async (params?: { search?: string; dept_id?: number; limit?: number; skip?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.search) searchParams.append('search', params.search);
    if (params?.dept_id != null) searchParams.append('dept_id', String(params.dept_id));
    if (params?.limit != null) searchParams.append('limit', String(params.limit));
    if (params?.skip != null) searchParams.append('skip', String(params.skip));
    const q = searchParams.toString();
    return apiRequest<AdminPersonListItem[]>(`/admin/persons${q ? `?${q}` : ''}`, { method: 'GET' });
  },
  getPerson: async (personId: string) => {
    return apiRequest<any>(`/admin/persons/${personId}`, { method: 'GET' });
  },
  getPersonDocs: async (personId: string) => {
    return apiRequest<{ items: AdminPersonDocItem[] }>(`/admin/persons/${personId}/documents`, { method: 'GET' });
  },
  downloadDoc: async (documentId: number, filename: string) => {
    const response = await apiFetch(`/admin/documents/${documentId}/download`, { method: 'GET' });
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(err.detail || err.message || `HTTP ${response.status}`);
    }
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || `document-${documentId}`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },
};

export interface AuditLogFilters {
  date_from?: string;
  date_to?: string;
  action_type?: string;
  entity_type?: string;
  actor_user_id?: number;
  dept_id?: number;
  search?: string;
  page?: number;
  page_size?: number;
  sort?: string;
}

export interface AuditLogItem {
  id: string;
  actor_user_id?: number;
  action_type: string;
  entity_type: string;
  entity_id?: string;
  action_metadata?: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
  actor_name?: string;
  actor_email?: string;
  actor_dept_id?: number;
  actor_dept_name?: string;
}

export interface AuditLogListResponse {
  items: AuditLogItem[];
  page: number;
  page_size: number;
  total: number;
}

export const audit = {
  fetchLogs: async (filters: AuditLogFilters) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params.append(key, String(value));
      }
    });
    const queryString = params.toString();
    return apiRequest<AuditLogListResponse>(`/audit/logs${queryString ? `?${queryString}` : ''}`, {
      method: 'GET',
    });
  },
  
  exportLogs: async (filters: AuditLogFilters, format: 'csv' | 'xlsx' = 'csv') => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '' && key !== 'page' && key !== 'page_size' && key !== 'sort') {
        params.append(key, String(value));
      }
    });
    params.append('format', format);
    const queryString = params.toString();
    const response = await apiFetch(`/audit/logs/export?${queryString}`, { method: 'GET' });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || errorData.message || `HTTP error! status: ${response.status}`);
    }
    
    const blob = await response.blob();
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = `audit_logs_${new Date().toISOString().split('T')[0]}.${format}`;
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1].replace(/['"]/g, '');
      }
    }
    
    const url_obj = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url_obj;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url_obj);
    document.body.removeChild(a);
    
    return { success: true };
  },
};

