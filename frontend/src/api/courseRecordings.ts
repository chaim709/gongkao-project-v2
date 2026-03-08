import client from './client';
import type { Teacher, Subject, ClassType, ClassBatch, CourseRecording } from '../types/courseRecording';

export const courseRecordingApi = {
  // Teachers
  listTeachers: (params: { page: number; page_size: number }) =>
    client.get('/teachers', { params }).then((res) => res.data),

  createTeacher: (data: Partial<Teacher>) =>
    client.post('/teachers', data).then((res) => res.data),

  updateTeacher: (id: number, data: Partial<Teacher>) =>
    client.put(`/teachers/${id}`, data).then((res) => res.data),

  deleteTeacher: (id: number) =>
    client.delete(`/teachers/${id}`),

  // Subjects
  listSubjects: () =>
    client.get('/subjects').then((res) => res.data),

  createSubject: (data: Partial<Subject>) =>
    client.post('/subjects', data).then((res) => res.data),

  // Class Types
  listClassTypes: () =>
    client.get('/class-types').then((res) => res.data),

  createClassType: (data: Partial<ClassType>) =>
    client.post('/class-types', data).then((res) => res.data),

  // Class Batches
  listClassBatches: (params: { page: number; page_size: number; status?: string }) =>
    client.get('/class-batches', { params }).then((res) => res.data),

  createClassBatch: (data: Partial<ClassBatch>) =>
    client.post('/class-batches', data).then((res) => res.data),

  updateClassBatch: (id: number, data: Partial<ClassBatch>) =>
    client.put(`/class-batches/${id}`, data).then((res) => res.data),

  deleteClassBatch: (id: number) =>
    client.delete(`/class-batches/${id}`),

  // Course Recordings
  listCourseRecordings: (params: { page: number; page_size: number; batch_id?: number }) =>
    client.get('/course-recordings', { params }).then((res) => res.data),

  createCourseRecording: (data: Partial<CourseRecording>) =>
    client.post('/course-recordings', data).then((res) => res.data),

  updateCourseRecording: (id: number, data: Partial<CourseRecording>) =>
    client.put(`/course-recordings/${id}`, data).then((res) => res.data),

  deleteCourseRecording: (id: number) =>
    client.delete(`/course-recordings/${id}`),
};
