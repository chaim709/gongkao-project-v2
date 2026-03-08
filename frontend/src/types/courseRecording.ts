export interface Teacher {
  id: number;
  name: string;
  phone?: string;
  wechat?: string;
  subject_ids?: string;
  title?: string;
  bio?: string;
  status: string;
  created_at: string;
  updated_at?: string;
}

export interface Subject {
  id: number;
  name: string;
  code?: string;
  category?: string;
  description?: string;
  sort_order: number;
  created_at: string;
}

export interface ClassType {
  id: number;
  name: string;
  description?: string;
  duration_days?: number;
  price?: number;
  status: string;
  created_at: string;
}

export interface ClassBatch {
  id: number;
  name: string;
  class_type_id?: number;
  class_type_name?: string;
  start_date?: string;
  end_date?: string;
  teacher_id?: number;
  teacher_name?: string;
  student_count: number;
  status: string;
  description?: string;
  created_at: string;
}

export interface CourseRecording {
  id: number;
  batch_id?: number;
  batch_name?: string;
  schedule_id?: number;
  recording_date: string;
  period?: string;
  title: string;
  recording_url?: string;
  subject_id?: number;
  subject_name?: string;
  teacher_id?: number;
  teacher_name?: string;
  duration_minutes?: number;
  remark?: string;
  created_by?: number;
  created_at: string;
}
