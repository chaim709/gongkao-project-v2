import client from './client';
import type { Attendance } from '../types/attendance';

export const attendanceApi = {
  listAttendances: (params: {
    page: number;
    page_size: number;
    student_id?: number;
    status?: string;
    start_date?: string;
    end_date?: string;
  }) =>
    client.get('/attendances', { params }).then((res) => res.data),

  createAttendance: (data: Partial<Attendance>) =>
    client.post('/attendances', data).then((res) => res.data),

  updateAttendance: (id: number, data: Partial<Attendance>) =>
    client.put(`/attendances/${id}`, data).then((res) => res.data),

  deleteAttendance: (id: number) =>
    client.delete(`/attendances/${id}`),
};
