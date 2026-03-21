/**
 * ## 용도
 * Zustand 기반 Auth 상태 관리 + localStorage 토큰 영속성.
 * login, signup, logout, withdraw, refreshTokens, loadUser.
 *
 * ## 사용법
 * 1. authApi에 login, signup, refresh, getMe, withdraw 함수 구현
 * 2. App 마운트 시 loadUser() 호출
 * 3. 컴포넌트에서 useAuthStore() 사용
 *
 * ## 출처
 * stock-dashboard/frontend/src/store/authStore.ts
 */

import { create } from "zustand";
import * as authApi from "../api/auth";

const STORAGE_KEY = "auth_tokens";

function loadTokens() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (parsed.accessToken && parsed.refreshToken) return parsed;
    return null;
  } catch {
    return null;
  }
}

function saveTokens(accessToken: string, refreshToken: string) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ accessToken, refreshToken }));
}

function clearTokens() {
  localStorage.removeItem(STORAGE_KEY);
}

const savedTokens = loadTokens();

export const useAuthStore = create((set, get) => ({
  user: null,
  accessToken: savedTokens?.accessToken ?? null,
  refreshToken: savedTokens?.refreshToken ?? null,
  isLoading: false,

  setTokens: (tokens) => {
    saveTokens(tokens.access_token, tokens.refresh_token);
    set({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
  },

  login: async (email, password) => {
    set({ isLoading: true });
    try {
      const tokens = await authApi.login({ email, password });
      get().setTokens(tokens);
      const user = await authApi.getMe();
      set({ user, isLoading: false });
    } catch (err) {
      set({ isLoading: false });
      throw err;
    }
  },

  logout: () => {
    clearTokens();
    set({ user: null, accessToken: null, refreshToken: null });
  },

  withdraw: async (password) => {
    await authApi.withdraw(password);
    clearTokens();
    set({ user: null, accessToken: null, refreshToken: null });
  },

  // 401 시 refresh 시도 → 실패하면 로그아웃
  refreshTokens: async () => {
    const { refreshToken } = get();
    if (!refreshToken) return false;
    try {
      const tokens = await authApi.refresh(refreshToken);
      get().setTokens(tokens);
      return true;
    } catch {
      get().logout();
      return false;
    }
  },

  // 앱 마운트 시 호출 — 토큰 유효성 확인 + 자동 갱신
  loadUser: async () => {
    const { accessToken } = get();
    if (!accessToken) return;
    set({ isLoading: true });
    try {
      const user = await authApi.getMe();
      set({ user, isLoading: false });
    } catch {
      const refreshed = await get().refreshTokens();
      if (refreshed) {
        try {
          const user = await authApi.getMe();
          set({ user, isLoading: false });
        } catch {
          set({ isLoading: false });
        }
      } else {
        set({ isLoading: false });
      }
    }
  },
}));
