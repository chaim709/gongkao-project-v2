import client from './client';
import type { CheckinResponse, CheckinStats, CheckinRankItem } from '../types/checkin';

export const checkinApi = {
  checkin: (data: { student_id: number; checkin_date?: string; content?: string }) =>
    client.post<CheckinResponse, typeof data>('/checkins', data),

  getStats: (studentId: number) =>
    client.get<any, CheckinStats>(`/checkins/stats/${studentId}`),

  getRank: (limit: number = 20) =>
    client.get<any, { items: CheckinRankItem[] }>('/checkins/rank', { params: { limit } }),
};
