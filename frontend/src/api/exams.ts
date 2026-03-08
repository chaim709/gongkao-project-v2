import client from './client';

export const examApi = {
  // 试卷管理
  listPapers: (params: {
    page: number; page_size: number;
    subject?: string; exam_type?: string; year?: number; search?: string;
  }) =>
    client.get('/exams/papers', { params }),

  getPaper: (id: number) =>
    client.get(`/exams/papers/${id}`),

  createPaper: (data: {
    title: string; subject: string; total_questions: number;
    exam_type?: string; time_limit?: number; year?: number; source?: string; description?: string;
  }) =>
    client.post('/exams/papers', data),

  getPaperQrcode: (id: number) =>
    `/api/v1/exams/papers/${id}/qrcode`,

  // 题目管理
  listQuestions: (params: {
    page: number; page_size: number;
    paper_id?: number; category?: string; subcategory?: string;
    knowledge_point?: string; difficulty?: string; search?: string;
  }) =>
    client.get('/exams/questions', { params }),

  createQuestion: (data: Record<string, unknown>) =>
    client.post('/exams/questions', data),

  batchCreateQuestions: (questions: Record<string, unknown>[]) =>
    client.post('/exams/questions/batch', questions),

  updateQuestion: (id: number, data: Record<string, unknown>) =>
    client.put(`/exams/questions/${id}`, data),

  // 知识点标签
  getKnowledgeTags: () =>
    client.get('/exams/knowledge-tags'),

  // 学员分析
  getStudentAnalysis: (studentId: number) =>
    client.get(`/exams/analysis/student/${studentId}`),

  // 模考成绩
  listScores: (params: {
    page: number; page_size: number;
    paper_id?: number; student_id?: number;
  }) =>
    client.get('/exams/scores', { params }),

  createScore: (data: {
    student_id: number; paper_id: number;
    correct_count?: number; wrong_count?: number;
    time_used?: number; score_detail?: Record<string, number>;
  }) =>
    client.post('/exams/scores', data),

  // AI 解析
  aiParse: (file: File, subject?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (subject) formData.append('subject', subject);
    return client.post('/exams/ai-parse', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    });
  },

  // 班级分析
  getClassAnalysis: (paperId?: number) =>
    client.get('/exams/analysis/class', { params: paperId ? { paper_id: paperId } : {} }),
};
