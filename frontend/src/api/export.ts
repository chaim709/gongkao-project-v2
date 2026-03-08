import axios from 'axios';

const downloadFile = async (url: string, params: Record<string, unknown>, filename: string) => {
  const token = localStorage.getItem('token');
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1';
  const resp = await axios.get(`${baseURL}${url}`, {
    params,
    responseType: 'blob',
    headers: { Authorization: `Bearer ${token}` },
  });
  const blob = new Blob([resp.data]);
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
};

export const exportApi = {
  students: (params: { status?: string } = {}) =>
    downloadFile('/export/students', params, '学员列表.xlsx'),

  finance: (params: { record_type?: string; year?: number; month?: number } = {}) =>
    downloadFile('/export/finance', params, '财务记录.xlsx'),

  attendances: (params: { start_date?: string; end_date?: string } = {}) =>
    downloadFile('/export/attendances', params, '考勤记录.xlsx'),
};
