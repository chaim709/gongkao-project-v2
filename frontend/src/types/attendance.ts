export interface Attendance {
  id: number;
  student_id: number;
  student_name?: string;
  course_id?: number;
  course_name?: string;
  attendance_date: string;
  status: string;
  notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface AttendanceCreate {
  student_id: number;
  course_id?: number;
  attendance_date: string;
  status: string;
  notes?: string;
}
