import { create } from 'zustand';
import { authApi } from '../api/auth';
import type { User } from '../api/auth';

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  setUser: (user: User) => void;
  fetchUser: () => Promise<void>;
  refresh: () => Promise<boolean>;
}

function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp * 1000 < Date.now();
  } catch {
    return true;
  }
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: localStorage.getItem('token'),
  refreshToken: localStorage.getItem('refreshToken'),
  user: null,
  isAuthenticated: !!localStorage.getItem('token'),
  loading: false,

  login: async (username, password) => {
    const response = await authApi.login({ username, password });
    localStorage.setItem('token', response.access_token);
    localStorage.setItem('refreshToken', response.refresh_token);
    set({
      token: response.access_token,
      refreshToken: response.refresh_token,
      user: response.user,
      isAuthenticated: true,
    });
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    set({ token: null, refreshToken: null, user: null, isAuthenticated: false });
  },

  setUser: (user) => set({ user }),

  fetchUser: async () => {
    const { token, refresh } = get();
    if (!token || get().user) return;

    // 检查 access token 是否过期，过期则尝试刷新
    if (isTokenExpired(token)) {
      const refreshed = await refresh();
      if (!refreshed) return;
    }

    set({ loading: true });
    try {
      const user = await authApi.getMe();
      set({ user, isAuthenticated: true, loading: false });
    } catch {
      // 尝试刷新 token
      const refreshed = await refresh();
      if (refreshed) {
        try {
          const user = await authApi.getMe();
          set({ user, isAuthenticated: true, loading: false });
          return;
        } catch { /* fall through to logout */ }
      }
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      set({ token: null, refreshToken: null, user: null, isAuthenticated: false, loading: false });
    }
  },

  refresh: async () => {
    const refreshToken = get().refreshToken;
    if (!refreshToken || isTokenExpired(refreshToken)) {
      get().logout();
      return false;
    }
    try {
      const response = await authApi.refresh(refreshToken);
      localStorage.setItem('token', response.access_token);
      localStorage.setItem('refreshToken', response.refresh_token);
      set({
        token: response.access_token,
        refreshToken: response.refresh_token,
        user: response.user,
        isAuthenticated: true,
      });
      return true;
    } catch {
      get().logout();
      return false;
    }
  },
}));
