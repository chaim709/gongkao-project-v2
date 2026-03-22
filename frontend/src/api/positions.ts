import client from './client';
import type { MatchResult, ShiyeSelectionFilterOptions } from '../types/position';

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

  shiyeSelectionSearch: (params: {
    year: number;
    education: string;
    major: string;
    political_status?: string;
    work_years?: number;
    gender?: string;
    city?: string;
    location?: string;
    exam_category?: string;
    funding_source?: string;
    recruitment_target?: string;
    post_natures?: string[];
    recommendation_tiers?: string[];
    include_manual_review?: boolean;
    page?: number;
    page_size?: number;
    sort_by?: string;
    sort_order?: string;
  }) => client.post<MatchResult>('/positions/shiye-selection/search', params),

  shiyeFilterOptions: (params: { year: number }) =>
    client.get<ShiyeSelectionFilterOptions>('/positions/shiye-selection/filter-options', { params }),

  // 岗位对比
  compare: (positionIds: number[]) =>
    client.post('/positions/compare', { position_ids: positionIds }),

  // 生成选岗报告 PDF
  generateReport: async (data: {
    student_id: number;
    position_ids: number[];
    year: number;
    exam_type: string;
    education?: string;
    major?: string;
    political_status?: string;
    work_years?: number;
    gender?: string;
    city?: string;
    location?: string;
    exam_category?: string;
    funding_source?: string;
    recruitment_target?: string;
    post_natures?: string[];
    recommendation_tiers?: string[];
    include_manual_review?: boolean;
    sort_by?: string;
    sort_order?: string;
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
