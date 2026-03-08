export interface Student {
  id: number;
  name: string;
  phone?: string;
  wechat?: string;
  gender?: '男' | '女';
  education?: '高中' | '大专' | '本科' | '硕士' | '博士';
  major?: string;
  exam_type?: string;
  supervisor_id?: number;
  need_attention?: boolean;
  status: 'active' | 'inactive' | 'graduated';
  enrollment_date?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface StudentCreate {
  name: string;
  phone?: string;
  wechat?: string;
  gender?: '男' | '女';
  education?: '高中' | '大专' | '本科' | '硕士' | '博士';
  major?: string;
  exam_type?: string;
  supervisor_id?: number;
  enrollment_date?: string;
  notes?: string;
}

export interface StudentUpdate extends Partial<StudentCreate> {
  need_attention?: boolean;
  status?: 'active' | 'inactive' | 'graduated';
}

export interface StudentListResponse {
  items: Student[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface StudentListParams {
  page?: number;
  page_size?: number;
  search?: string;
  status?: string;
  supervisor_id?: number;
}
