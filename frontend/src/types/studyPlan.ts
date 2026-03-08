export interface StudyPlan {
  id: number;
  student_id: number;
  student_name?: string;
  name: string;
  phase?: string;
  start_date: string;
  end_date?: string;
  status: string;
  ai_suggestion?: string;
  notes?: string;
  created_by?: number;
  creator_name?: string;
  created_at: string;
  updated_at: string;
  task_count: number;
  completed_task_count: number;
}

export interface StudyPlanCreate {
  student_id: number;
  name: string;
  phase?: string;
  start_date: string;
  end_date?: string;
  ai_suggestion?: string;
  notes?: string;
}

export interface PlanTask {
  id: number;
  plan_id: number;
  title: string;
  description?: string;
  task_type?: string;
  target_value?: number;
  actual_value: number;
  due_date?: string;
  status: string;
  priority: number;
  created_at: string;
  updated_at: string;
}

export interface PlanTaskCreate {
  plan_id: number;
  title: string;
  description?: string;
  task_type?: string;
  target_value?: number;
  due_date?: string;
  priority?: number;
}
