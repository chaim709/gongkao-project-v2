import client from './client';

interface AuditLog {
  id: number;
  user_id: number;
  user_name?: string;
  action: string;
  resource_type: string;
  resource_id?: number;
  old_value?: Record<string, unknown>;
  new_value?: Record<string, unknown>;
  ip_address?: string;
  created_at: string;
}

interface AuditLogListParams {
  page: number;
  page_size: number;
  user_id?: number;
  action?: string;
  resource_type?: string;
}

export type { AuditLog, AuditLogListParams };

export const auditLogApi = {
  list: async (params: AuditLogListParams) => {
    const { data } = await client.get('/audit-logs', { params });
    return data as { items: AuditLog[]; total: number; page: number; page_size: number };
  },
};
