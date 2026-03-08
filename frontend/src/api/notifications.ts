import client from './client';

export const notificationApi = {
  list: (params: { page?: number; page_size?: number; is_read?: boolean }) =>
    client.get('/notifications', { params }),

  unreadCount: () =>
    client.get('/notifications/unread-count'),

  markRead: (id: number) =>
    client.put(`/notifications/${id}/read`),

  markAllRead: () =>
    client.put('/notifications/read-all'),

  create: (data: { title: string; content?: string; type?: string; user_id?: number }) =>
    client.post('/notifications', data),
};
