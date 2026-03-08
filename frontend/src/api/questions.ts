import client from './client';
import type { Question, Workbook } from '../types/question';

export const questionApi = {
  listQuestions: (params: { page: number; page_size: number; category?: string; difficulty?: string }) =>
    client.get('/questions', { params }).then((res) => res.data),

  createQuestion: (data: Partial<Question>) =>
    client.post('/questions', data).then((res) => res.data),

  updateQuestion: (id: number, data: Partial<Question>) =>
    client.put(`/questions/${id}`, data).then((res) => res.data),

  deleteQuestion: (id: number) =>
    client.delete(`/questions/${id}`),

  listWorkbooks: (params: { page: number; page_size: number }) =>
    client.get('/workbooks', { params }).then((res) => res.data),

  createWorkbook: (data: Partial<Workbook>) =>
    client.post('/workbooks', data).then((res) => res.data),

  updateWorkbook: (id: number, data: Partial<Workbook>) =>
    client.put(`/workbooks/${id}`, data).then((res) => res.data),

  deleteWorkbook: (id: number) =>
    client.delete(`/workbooks/${id}`),

  listWorkbookItems: (workbookId: number) =>
    client.get(`/workbooks/${workbookId}/items`).then((res) => res.data),

  addQuestionToWorkbook: (workbookId: number, data: any) =>
    client.post(`/workbooks/${workbookId}/items`, data).then((res) => res.data),

  removeQuestionFromWorkbook: (itemId: number) =>
    client.delete(`/workbook-items/${itemId}`),
};
