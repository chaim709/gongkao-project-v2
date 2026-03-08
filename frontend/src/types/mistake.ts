export interface Mistake {
  id: number;
  student_id: number;
  student_name?: string;
  question_id?: number;
  workbook_id?: number;
  submission_id?: number;
  question_order?: number;
  wrong_answer?: string;
  review_count: number;
  last_review_at?: string;
  mastered: boolean;
  notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface MistakeCreate {
  student_id: number;
  question_id?: number;
  workbook_id?: number;
  submission_id?: number;
  question_order?: number;
  wrong_answer?: string;
  notes?: string;
}

export interface MistakeReview {
  id: number;
  mistake_id: number;
  student_id: number;
  review_date: string;
  is_correct: boolean;
  time_spent?: number;
  notes?: string;
  created_at: string;
}
