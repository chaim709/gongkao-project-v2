import client from './client';
import type {
  SupervisionLog,
  SupervisionLogCreate,
  SupervisionLogListResponse,
  SupervisionLogListParams,
  ReminderListResponse,
} from '../types/supervision';

export const supervisionApi = {
  list: (params: SupervisionLogListParams = {}) =>
    client.get<any, SupervisionLogListResponse>('/supervision-logs', { params }),

  getById: (id: number) =>
    client.get<any, SupervisionLog>(`/supervision-logs/${id}`),

  create: (data: SupervisionLogCreate) =>
    client.post<SupervisionLog, SupervisionLogCreate>('/supervision-logs', data),

  delete: (id: number) =>
    client.delete(`/supervision-logs/${id}`),

  getReminders: (days: number = 7, supervisorId?: number) =>
    client.get<any, ReminderListResponse>('/supervision-logs/reminders', {
      params: { days, supervisor_id: supervisorId },
    }),
};
