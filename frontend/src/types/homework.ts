export interface Homework {
  id: number;
  course_id: number;
  course_name?: string;
  title: string;
  description?: string;
  due_date?: string;
  created_by?: number;
  creator_name?: string;
  created_at: string;
  submission_count: number;
  reviewed_count: number;
}

export interface HomeworkCreate {
  course_id: number;
  title: string;
  description?: string;
  due_date?: string;
}

export interface HomeworkListResponse {
  items: Homework[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface HomeworkListParams {
  page?: number;
  page_size?: number;
  course_id?: number;
}

export interface Submission {
  id: number;
  homework_id: number;
  student_id: number;
  student_name?: string;
  content?: string;
  file_url?: string;
  submitted_at: string;
  score?: number;
  feedback?: string;
  reviewer_name?: string;
  reviewed_at?: string;
}
