import client from './client';
import type { RecruitmentInfoFilters } from '../types/recruitmentInfo';

export const recruitmentInfoApi = {
  getList: (params: RecruitmentInfoFilters) =>
    client.get('/recruitment-info', { params }),

  getDetail: (id: number) =>
    client.get(`/recruitment-info/${id}`),

  getFilters: () =>
    client.get('/recruitment-info/filters'),

  getCrawlerStatus: () =>
    client.get('/recruitment-info/crawler-status'),

  triggerCrawl: () =>
    client.post('/recruitment-info/crawl'),

  triggerLogin: (cookies: string) =>
    client.post('/recruitment-info/login', { cookies }),

  updateCrawlerConfig: (id: number, data: Record<string, unknown>) =>
    client.post(`/recruitment-info/crawler-config/${id}`, data),

  triggerAiAnalyze: () =>
    client.post('/recruitment-info/ai-analyze'),

  getAiLogs: (page = 1, pageSize = 20) =>
    client.get('/recruitment-info/ai-logs', { params: { page, page_size: pageSize } }),

  getCrawlLogs: (page = 1, pageSize = 20) =>
    client.get('/recruitment-info/crawl-logs', { params: { page, page_size: pageSize } }),
};
