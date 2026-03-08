import client from './client';
import type { Homework, HomeworkCreate, HomeworkListResponse, HomeworkListParams, Submission } from '../types/homework';

export const homeworkApi = {
  list: (params: HomeworkListParams = {}) =>
    client.get<any, HomeworkListResponse>('/homework', { params }),

  getById: (id: number) =>
    client.get<any, Homework>(`/homework/${id}`),

  create: (data: HomeworkCreate) =>
    client.post<Homework, HomeworkCreate>('/homework', data),

  delete: (id: number) =>
    client.delete(`/homework/${id}`),

  listSubmissions: (hwId: number) =>
    client.get<any, Submission[]>(`/homework/${hwId}/submissions`),

  review: (subId: number, data: { score: number; feedback?: string }) =>
    client.put<Submission, { score: number; feedback?: string }>(`/homework/submissions/${subId}/review`, data),
};
