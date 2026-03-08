import axios from 'axios';
import { message } from 'antd';

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const client = axios.create({
  baseURL,
  timeout: 15000,
});

// 请求拦截器：添加 token
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 标记是否正在刷新，避免并发刷新
let isRefreshing = false;
let pendingRequests: Array<(token: string) => void> = [];

// 响应拦截器：统一错误处理
client.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    const status = error.response?.status;
    const data = error.response?.data;
    const originalRequest = error.config;

    if (status === 401 && !originalRequest._retry) {
      const refreshToken = localStorage.getItem('refreshToken');
      if (refreshToken) {
        if (isRefreshing) {
          // 等待刷新完成后重试
          return new Promise((resolve) => {
            pendingRequests.push((newToken: string) => {
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
              originalRequest._retry = true;
              resolve(client(originalRequest));
            });
          });
        }

        isRefreshing = true;
        try {
          const res = await axios.post(`${baseURL}/auth/refresh`, { refresh_token: refreshToken });
          const newToken = res.data.access_token;
          const newRefreshToken = res.data.refresh_token;
          localStorage.setItem('token', newToken);
          localStorage.setItem('refreshToken', newRefreshToken);

          // 重试排队的请求
          pendingRequests.forEach((cb) => cb(newToken));
          pendingRequests = [];

          // 重试原始请求
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          originalRequest._retry = true;
          return client(originalRequest);
        } catch {
          // 刷新失败，清理并跳转登录
          pendingRequests = [];
          localStorage.removeItem('token');
          localStorage.removeItem('refreshToken');
          window.location.href = '/login';
          return Promise.reject(data || error.message);
        } finally {
          isRefreshing = false;
        }
      } else {
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
      }
    } else if (status === 422) {
      const detail = data?.detail;
      if (typeof detail === 'string') {
        message.error(detail);
      } else {
        message.error(data?.message || '参数格式不正确，请检查输入');
      }
    } else if (status === 429) {
      message.warning('操作过于频繁，请稍后再试');
    } else if (status === 403) {
      message.error('无权限执行此操作');
    } else if (status === 404) {
      message.error(data?.detail || '请求的资源不存在');
    } else if (status >= 500) {
      message.error('服务器异常，请稍后重试');
    } else if (status === 400) {
      message.error(data?.detail || data?.message || '请求参数有误');
    }
    return Promise.reject(data || error.message);
  }
);

export default client;
