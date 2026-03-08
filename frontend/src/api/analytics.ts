import client from './client';

interface OverviewData {
  students: {
    total: number;
    active: number;
    new_this_month: number;
    by_status: Record<string, number>;
    by_exam_type: Record<string, number>;
  };
  supervision: {
    logs_this_month: number;
  };
  checkins: {
    today: number;
  };
}

interface SupervisionStats {
  total_logs: number;
  by_supervisor: Array<{
    supervisor_id: number;
    supervisor_name: string;
    log_count: number;
  }>;
  mood_distribution: Record<string, number>;
  needs_followup: number;
}

interface TrendItem {
  date: string;
  count: number;
}

interface TrendsData {
  students: TrendItem[];
  supervision_logs: TrendItem[];
  checkins: TrendItem[];
}

export const analyticsApi = {
  overview: async (): Promise<OverviewData> => {
    return await client.get('/analytics/overview');
  },

  supervision: async (startDate?: string, endDate?: string): Promise<SupervisionStats> => {
    return await client.get('/analytics/supervision', {
      params: { start_date: startDate, end_date: endDate },
    });
  },

  trends: async (days: number = 30): Promise<TrendsData> => {
    return await client.get('/analytics/trends', { params: { days } });
  },

  financeTrend: (months: number = 6) =>
    client.get('/analytics/finance-trend', { params: { months } }),

  studentGrowth: (months: number = 6) =>
    client.get('/analytics/student-growth', { params: { months } }),
};
