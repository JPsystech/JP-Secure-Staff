const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  
  // FIXED: Don't set Content-Type for FormData (browser will set it with boundary)
  const isFormData = options.body instanceof FormData;
  
  const headers: HeadersInit = {
    ...options.headers,
  };
  
  // Only set Content-Type for JSON, not for FormData
  if (!isFormData) {
    headers['Content-Type'] = 'application/json';
  }
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
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
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    const response = await fetch(`${apiBase}/admin/documents/${documentId}/download`, {
      method: 'GET',
      headers: { Authorization: token ? `Bearer ${token}` : '' },
      credentials: 'include',
    });
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
    
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    const url = `${apiBase}/audit/logs/export?${queryString}`;
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
      },
      credentials: 'include',
    });
    
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

