import client from './client';
import type { Course, CourseCreate, CourseUpdate, CourseListResponse, CourseListParams } from '../types/course';

export const courseApi = {
  list: (params: CourseListParams = {}) =>
    client.get<any, CourseListResponse>('/courses', { params }),

  getById: (id: number) =>
    client.get<any, Course>(`/courses/${id}`),

  create: (data: CourseCreate) =>
    client.post<Course, CourseCreate>('/courses', data),

  update: (id: number, data: CourseUpdate) =>
    client.put<Course, CourseUpdate>(`/courses/${id}`, data),

  delete: (id: number) =>
    client.delete(`/courses/${id}`),
};
