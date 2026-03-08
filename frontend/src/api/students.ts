import client from './client';
import type { Student, StudentCreate, StudentUpdate, StudentListResponse, StudentListParams } from '../types/student';

export const studentApi = {
  list: (params: StudentListParams = {}) =>
    client.get<any, StudentListResponse>('/students', { params }),

  getById: (id: number) =>
    client.get<any, Student>(`/students/${id}`),

  create: (data: StudentCreate) =>
    client.post<Student, StudentCreate>('/students', data),

  update: (id: number, data: StudentUpdate) =>
    client.put<Student, StudentUpdate>(`/students/${id}`, data),

  delete: (id: number) =>
    client.delete(`/students/${id}`),

  changeStatus: (id: number, status: string, reason?: string) =>
    client.put(`/students/${id}/status`, { status, reason }),

  getReminders: (days: number = 7) =>
    client.get('/students/reminders/follow-up', { params: { days } }),

  getLifecycleStats: () =>
    client.get('/students/stats/lifecycle'),

  batchImport: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return client.post('/students/batch/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  batchAssignSupervisor: (student_ids: number[], supervisor_id: number) =>
    client.post('/students/batch/assign-supervisor', { student_ids, supervisor_id }),

  batchUpdateStatus: (student_ids: number[], status: string) =>
    client.post('/students/batch/update-status', { student_ids, status }),

  getReport: (id: number) =>
    client.get(`/students/${id}/report`),
};
