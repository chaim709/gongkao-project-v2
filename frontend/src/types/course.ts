export interface Course {
  id: number;
  name: string;
  course_type?: string;
  teacher_id?: number;
  teacher_name?: string;
  start_date?: string;
  end_date?: string;
  description?: string;
  status: string;
  created_at: string;
}

export interface CourseCreate {
  name: string;
  course_type?: string;
  teacher_id?: number;
  start_date?: string;
  end_date?: string;
  description?: string;
}

export interface CourseUpdate extends Partial<CourseCreate> {
  status?: 'active' | 'completed' | 'cancelled';
}

export interface CourseListResponse {
  items: Course[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface CourseListParams {
  page?: number;
  page_size?: number;
  search?: string;
  status?: string;
}
