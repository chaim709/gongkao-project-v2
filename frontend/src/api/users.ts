import client from './client';

export interface UserItem {
  id: number;
  username: string;
  real_name: string | null;
  role: string;
  phone: string | null;
  email: string | null;
  is_active: boolean;
  created_at: string | null;
}

export const userApi = {
  list: (params: { page?: number; page_size?: number; search?: string; role?: string } = {}) =>
    client.get('/users', { params }),

  getById: (id: number) =>
    client.get(`/users/${id}`),

  create: (data: { username: string; password: string; real_name?: string; role?: string; phone?: string; email?: string }) =>
    client.post('/users', data),

  update: (id: number, data: { real_name?: string; role?: string; phone?: string; email?: string; is_active?: boolean }) =>
    client.put(`/users/${id}`, data),

  resetPassword: (id: number, new_password: string) =>
    client.put(`/users/${id}/reset-password`, { new_password }),

  delete: (id: number) =>
    client.delete(`/users/${id}`),
};
