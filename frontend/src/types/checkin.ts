export interface CheckinResponse {
  id: number;
  student_id: number;
  student_name?: string;
  checkin_date: string;
  content?: string;
  created_at: string;
}

export interface CheckinStats {
  student_id: number;
  student_name: string;
  total_days: number;
  consecutive_days: number;
  checkin_dates: string[];
}

export interface CheckinRankItem {
  student_id: number;
  student_name: string;
  total_days: number;
  consecutive_days: number;
}
