import client from './client';
import type { Mistake, MistakeReview } from '../types/mistake';

export const mistakeApi = {
  list: (params: { page: number; page_size: number; student_id?: number; mastered?: boolean }) =>
    client.get('/mistakes', { params }).then((res) => res.data),

  create: (data: Partial<Mistake>) =>
    client.post('/mistakes', data).then((res) => res.data),

  update: (id: number, data: Partial<Mistake>) =>
    client.put(`/mistakes/${id}`, data).then((res) => res.data),

  delete: (id: number) =>
    client.delete(`/mistakes/${id}`),

  createReview: (mistakeId: number, data: Partial<MistakeReview>) =>
    client.post(`/mistakes/${mistakeId}/reviews`, data).then((res) => res.data),

  listReviews: (mistakeId: number) =>
    client.get(`/mistakes/${mistakeId}/reviews`).then((res) => res.data),
};
