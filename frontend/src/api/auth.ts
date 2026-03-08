import client from './client';

export interface LoginData {
  username: string;
  password: string;
}

export interface User {
  id: number;
  username: string;
  real_name?: string;
  role: string;
  phone?: string;
  email?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export const authApi = {
  login: (data: LoginData) => client.post<TokenResponse, LoginData>('/auth/login', data),
  getMe: () => client.get<User>('/auth/me'),
  logout: () => client.post('/auth/logout'),
  refresh: (refresh_token: string) =>
    client.post<TokenResponse, { refresh_token: string }>('/auth/refresh', { refresh_token }),
};
