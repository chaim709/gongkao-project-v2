export interface Question {
  id: number;
  stem: string;
  option_a?: string;
  option_b?: string;
  option_c?: string;
  option_d?: string;
  answer: string;
  analysis?: string;
  category?: string;
  subcategory?: string;
  knowledge_point?: string;
  difficulty?: string;
  source?: string;
  year?: number;
  is_image_question: boolean;
  image_path?: string;
  created_at: string;
  updated_at?: string;
}

export interface QuestionCreate {
  stem: string;
  option_a?: string;
  option_b?: string;
  option_c?: string;
  option_d?: string;
  answer: string;
  analysis?: string;
  category?: string;
  subcategory?: string;
  knowledge_point?: string;
  difficulty?: string;
  source?: string;
  year?: number;
  is_image_question?: boolean;
  image_path?: string;
}

export interface Workbook {
  id: number;
  name: string;
  description?: string;
  question_count: number;
  total_score: number;
  time_limit?: number;
  created_by?: number;
  creator_name?: string;
  created_at: string;
  updated_at?: string;
}

export interface WorkbookCreate {
  name: string;
  description?: string;
  category?: string;
}

export interface WorkbookItem {
  id: number;
  workbook_id: number;
  question_id: number;
  sort_order: number;
}
