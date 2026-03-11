import { create } from "zustand";
import type { User, TokenResponse } from "../types/auth";
import * as authApi from "../api/auth";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isLoading: boolean;

  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, nickname?: string) => Promise<void>;
  logout: () => void;
  refreshTokens: () => Promise<boolean>;
  loadUser: () => Promise<void>;
  setTokens: (tokens: TokenResponse) => void;
}

const STORAGE_KEY = "auth_tokens";

function loadTokens(): { accessToken: string; refreshToken: string } | null {
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

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: savedTokens?.accessToken ?? null,
  refreshToken: savedTokens?.refreshToken ?? null,
  isLoading: false,

  setTokens: (tokens: TokenResponse) => {
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

  signup: async (email, password, nickname) => {
    set({ isLoading: true });
    try {
      await authApi.signup({ email, password, nickname });
      // 회원가입 후 자동 로그인
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

  loadUser: async () => {
    const { accessToken } = get();
    if (!accessToken) return;
    set({ isLoading: true });
    try {
      const user = await authApi.getMe();
      set({ user, isLoading: false });
    } catch {
      // token 만료 시 refresh 시도
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
