import client from './client';

export const financeApi = {
  list: (params: {
    page: number; page_size: number;
    record_type?: string; category?: string;
    start_date?: string; end_date?: string;
  }) =>
    client.get('/finance', { params }),

  create: (data: {
    record_type: string; category: string; amount: number;
    record_date: string; description?: string;
    student_id?: number; payment_method?: string; receipt_no?: string;
  }) =>
    client.post('/finance', data),

  update: (id: number, data: Record<string, unknown>) =>
    client.put(`/finance/${id}`, data),

  delete: (id: number) =>
    client.delete(`/finance/${id}`),

  summary: (year?: number, month?: number) =>
    client.get('/finance/summary', { params: { year, month } }),
};
