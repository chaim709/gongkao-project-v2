import client from './client';
import type { Position } from '../types/position';

export const positionApi = {
  list: (params: {
    page: number; page_size: number;
    search?: string; year?: number; exam_type?: string;
    city?: string; education?: string;
    exam_category?: string; difficulty_level?: string;
    location?: string; province?: string; institution_level?: string;
    funding_source?: string; recruitment_target?: string;
    sort_by?: string; sort_order?: string;
  }) =>
    client.get('/positions', { params }),

  get: (id: number) =>
    client.get(`/positions/${id}`),

  create: (data: Partial<Position>) =>
    client.post('/positions', data),

  filterOptions: (params?: { year?: number; exam_type?: string }) =>
    client.get('/positions/filter-options', { params }),

  stats: (params?: { year?: number; exam_type?: string }) =>
    client.get('/positions/stats/overview', { params }),

  analysis: (id: number) =>
    client.get(`/positions/analysis/${id}`),

  recommend: (studentId: number, params?: {
    year?: number;
    exam_type?: string;
    limit?: number;
    strategy?: string;
  }) =>
    client.get(`/positions/recommend/${studentId}`, { params }),

  // 收藏
  getFavorites: (studentId: number) =>
    client.get(`/positions/favorites/${studentId}`),

  addFavorite: (data: { student_id: number; position_id: number; category?: string; note?: string }) =>
    client.post('/positions/favorites', data),

  removeFavorite: (favoriteId: number) =>
    client.delete(`/positions/favorites/${favoriteId}`),

  // 城市评级
  cityRatings: (params?: { year?: number; exam_type?: string }) =>
    client.get('/positions/city-ratings', { params }),

  // 智能导入
  smartImport: (files: File[], year: number, examType: string) => {
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
    return client.post(`/positions/smart-import?year=${year}&exam_type=${encodeURIComponent(examType)}`, formData);
  },

  // 条件匹配
  match: (params: {
    year: number; exam_type: string;
    education: string; major: string;
    political_status?: string; work_years?: number; gender?: string;
    city?: string; exam_category?: string; location?: string;
    province?: string; institution_level?: string;
    page?: number; page_size?: number;
    sort_by?: string; sort_order?: string;
  }) => client.post('/positions/match', params),

  matchForStudent: (studentId: number, params?: {
    year?: number; exam_type?: string;
    page?: number; page_size?: number;
    city?: string; exam_category?: string;
    sort_by?: string; sort_order?: string;
  }) => client.get(`/positions/match-for-student/${studentId}`, { params }),

  // 岗位对比
  compare: (positionIds: number[]) =>
    client.post('/positions/compare', { position_ids: positionIds }),

  // 生成选岗报告 PDF
  generateReport: async (data: {
    student_id: number;
    position_ids: number[];
    year: number;
    exam_type: string;
  }) => {
    const res = await client.post('/positions/report/pdf', data, {
      responseType: 'blob',
    });
    const blob = new Blob([res as any], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `选岗报告_${new Date().toISOString().slice(0, 10)}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  },
};
