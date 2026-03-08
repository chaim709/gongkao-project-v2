import client from './client';

export const calendarApi = {
  list: (params: { year: number; month: number; event_type?: string }) =>
    client.get('/calendar', { params }),

  upcoming: (days: number = 90) =>
    client.get('/calendar/upcoming', { params: { days } }),

  create: (data: {
    title: string;
    description?: string;
    event_type?: string;
    exam_category?: string;
    province?: string;
    start_date: string;
    end_date?: string;
    start_time?: string;
    end_time?: string;
    is_all_day?: boolean;
    color?: string;
    remind_before?: number;
    is_public?: boolean;
    source?: string;
    source_url?: string;
  }) => client.post('/calendar', data),

  update: (id: number, data: any) =>
    client.put(`/calendar/${id}`, data),

  delete: (id: number) =>
    client.delete(`/calendar/${id}`),

  aiParse: (text: string) =>
    client.post('/calendar/ai-parse', { text }),

  confirmAiEvents: (events: any[]) =>
    client.post('/calendar/ai-parse/confirm', events),
};
