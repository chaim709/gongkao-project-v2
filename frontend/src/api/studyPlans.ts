import client from './client';
import type { StudyPlanCreate, PlanTaskCreate } from '../types/studyPlan';

export const studyPlanApi = {
  list: (params: { page: number; page_size: number; student_id?: number; status?: string }) =>
    client.get('/study-plans', { params }).then((res) => res.data),

  create: (data: StudyPlanCreate) =>
    client.post('/study-plans', data).then((res) => res.data),

  get: (id: number) =>
    client.get(`/study-plans/${id}`).then((res) => res.data),

  update: (id: number, data: Partial<StudyPlanCreate>) =>
    client.put(`/study-plans/${id}`, data).then((res) => res.data),

  delete: (id: number) =>
    client.delete(`/study-plans/${id}`),

  listTasks: (planId: number) =>
    client.get(`/study-plans/${planId}/tasks`).then((res) => res.data),

  createTask: (planId: number, data: Omit<PlanTaskCreate, 'plan_id'>) =>
    client.post(`/study-plans/${planId}/tasks`, data).then((res) => res.data),

  updateTask: (taskId: number, data: Partial<PlanTaskCreate>) =>
    client.put(`/plan-tasks/${taskId}`, data).then((res) => res.data),

  deleteTask: (taskId: number) =>
    client.delete(`/plan-tasks/${taskId}`),
};
