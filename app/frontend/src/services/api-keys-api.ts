import { API_BASE_URL, getAuthHeaders, getAuthOnlyHeaders } from '@/services/api-config';

export interface ApiKey {
  id: number;
  provider: string;
  key_value: string;
  is_active: boolean;
  description?: string;
  created_at: string;
  updated_at?: string;
  last_used?: string;
}

export interface ApiKeySummary {
  id: number;
  provider: string;
  is_active: boolean;
  description?: string;
  created_at: string;
  updated_at?: string;
  last_used?: string;
  has_key: boolean;
}

export interface ApiKeyCreateRequest {
  provider: string;
  key_value: string;
  description?: string;
  is_active: boolean;
}

export interface ApiKeyUpdateRequest {
  key_value?: string;
  description?: string;
  is_active?: boolean;
}

export interface ApiKeyBulkUpdateRequest {
  api_keys: ApiKeyCreateRequest[];
}

class ApiKeysService {
  private baseUrl = `${API_BASE_URL}/api-keys`;

  async getAllApiKeys(includeInactive = false): Promise<ApiKeySummary[]> {
    const params = new URLSearchParams();
    if (includeInactive) {
      params.append('include_inactive', 'true');
    }
    
    const response = await fetch(`${this.baseUrl}?${params}`, {
      headers: getAuthOnlyHeaders(),
    });
    if (!response.ok) {
      throw new Error(`Failed to fetch API keys: ${response.statusText}`);
    }
    return response.json();
  }

  async getApiKey(provider: string): Promise<ApiKey> {
    const response = await fetch(`${this.baseUrl}/${encodeURIComponent(provider)}`, {
      headers: getAuthOnlyHeaders(),
    });
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('API key not found');
      }
      throw new Error(`Failed to fetch API key: ${response.statusText}`);
    }
    return response.json();
  }

  async createOrUpdateApiKey(request: ApiKeyCreateRequest): Promise<ApiKey> {
    const response = await fetch(this.baseUrl, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to create/update API key: ${response.statusText}`);
    }
    return response.json();
  }

  async updateApiKey(provider: string, request: ApiKeyUpdateRequest): Promise<ApiKey> {
    const response = await fetch(`${this.baseUrl}/${encodeURIComponent(provider)}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('API key not found');
      }
      throw new Error(`Failed to update API key: ${response.statusText}`);
    }
    return response.json();
  }

  async deleteApiKey(provider: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/${encodeURIComponent(provider)}`, {
      method: 'DELETE',
      headers: getAuthOnlyHeaders(),
    });
    
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('API key not found');
      }
      throw new Error(`Failed to delete API key: ${response.statusText}`);
    }
  }

  async deactivateApiKey(provider: string): Promise<ApiKeySummary> {
    const response = await fetch(`${this.baseUrl}/${encodeURIComponent(provider)}/deactivate`, {
      method: 'PATCH',
      headers: getAuthOnlyHeaders(),
    });
    
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('API key not found');
      }
      throw new Error(`Failed to deactivate API key: ${response.statusText}`);
    }
    return response.json();
  }

  async bulkUpdateApiKeys(request: ApiKeyBulkUpdateRequest): Promise<ApiKey[]> {
    const response = await fetch(`${this.baseUrl}/bulk`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to bulk update API keys: ${response.statusText}`);
    }
    return response.json();
  }

  async updateLastUsed(provider: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/${encodeURIComponent(provider)}/last-used`, {
      method: 'PATCH',
      headers: getAuthOnlyHeaders(),
    });
    
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('API key not found');
      }
      throw new Error(`Failed to update last used timestamp: ${response.statusText}`);
    }
  }
}

export const apiKeysService = new ApiKeysService(); 