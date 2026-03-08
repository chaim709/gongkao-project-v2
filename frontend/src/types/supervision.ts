export interface SupervisionLog {
  id: number;
  student_id: number;
  supervisor_id: number;
  log_date: string;
  contact_method?: 'phone' | 'wechat' | 'meeting';
  mood?: 'positive' | 'stable' | 'anxious' | 'down';
  study_status?: 'excellent' | 'good' | 'average' | 'poor';
  content: string;
  next_followup_date?: string;
  created_at: string;
  student_name?: string;
  supervisor_name?: string;
}

export interface SupervisionLogCreate {
  student_id: number;
  log_date: string;
  contact_method?: string;
  mood?: string;
  study_status?: string;
  content: string;
  next_followup_date?: string;
}

export interface SupervisionLogListResponse {
  items: SupervisionLog[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SupervisionLogListParams {
  page?: number;
  page_size?: number;
  student_id?: number;
  supervisor_id?: number;
  start_date?: string;
  end_date?: string;
}

export interface ReminderItem {
  student_id: number;
  student_name: string;
  last_contact_date?: string;
  days_since_contact: number;
  need_attention: boolean;
  supervisor_name?: string;
}

export interface ReminderListResponse {
  items: ReminderItem[];
  total: number;
}
