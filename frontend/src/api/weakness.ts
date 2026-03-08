import client from './client';

export interface ModuleCategory {
  id: number;
  level1: string;
  level2?: string;
  exam_type?: string;
}

export interface WeaknessTag {
  id: number;
  student_id: number;
  module_id?: number;
  module_name: string;
  sub_module_name?: string;
  level: 'red' | 'yellow' | 'green';
  accuracy_rate?: number;
  practice_count: number;
  created_at?: string;
  updated_at?: string;
}

export interface WeaknessTagCreate {
  module_name: string;
  sub_module_name?: string;
  level: string;
  accuracy_rate?: number;
  practice_count?: number;
  module_id?: number;
}

export interface ModuleTreeNode {
  title: string;
  value: string;
  selectable?: boolean;
  children?: ModuleTreeNode[];
  id?: number;
}

export interface WeaknessRadarItem {
  module: string;
  accuracy: number;
  mastery: number;
  practice_count: number;
  sub_count: number;
  red: number;
  yellow: number;
  green: number;
}

export const weaknessApi = {
  getModules: (examType?: string) =>
    client.get<any, ModuleCategory[]>('/modules', { params: { exam_type: examType } }),

  getModuleTree: (examType?: string) =>
    client.get<any, { tree: ModuleTreeNode[] }>('/modules/tree', { params: { exam_type: examType } }),

  getStudentWeaknesses: (studentId: number) =>
    client.get<any, WeaknessTag[]>(`/students/${studentId}/weaknesses`),

  getWeaknessRadar: (studentId: number) =>
    client.get<any, { items: WeaknessRadarItem[]; summary: Record<string, number> }>(`/students/${studentId}/weakness-radar`),

  createWeakness: (studentId: number, data: WeaknessTagCreate) =>
    client.post<WeaknessTag, WeaknessTagCreate>(`/students/${studentId}/weaknesses`, data),

  updateWeakness: (tagId: number, data: Partial<WeaknessTagCreate>) =>
    client.put<WeaknessTag, Partial<WeaknessTagCreate>>(`/weaknesses/${tagId}`, data),

  deleteWeakness: (tagId: number) =>
    client.delete(`/weaknesses/${tagId}`),
};
