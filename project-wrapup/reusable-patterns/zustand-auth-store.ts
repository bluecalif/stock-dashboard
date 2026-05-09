/**
 * ## 용도
 * Zustand 기반 Auth 상태 관리 + localStorage 토큰 영속성.
 * login, logout, withdraw, refreshTokens, loadUser 전체 플로우.
 *
 * ## 언제 쓰는가
 * React + JWT 인증 프로젝트에서 전역 인증 상태를 관리할 때.
 * 페이지 새로고침 후에도 로그인 상태를 유지해야 할 때.
 *
 * ## 전제조건
 * - JWT 기반 백엔드 인증 API (login, refresh, getMe, withdraw)
 * - axios-interceptor-refresh.ts로 토큰 자동 주입 설정
 *
 * ## 의존성
 * - zustand: 상태 관리 라이브러리
 * - authApi: login, signup, refresh, getMe, withdraw API 함수
 * - localStorage: auth_tokens 키로 토큰 저장
 *
 * ## 통합 포인트
 * - store/ 디렉토리에 배치
 * - App.tsx에서 useEffect로 loadUser() 호출 (앱 마운트 시)
 * - 인증 필요 컴포넌트에서 useAuthStore() 사용
 * - axios-interceptor-refresh.ts와 localStorage 키(auth_tokens) 공유
 *
 * ## 주의사항
 * - loadUser는 앱 마운트 시 1회만 호출. 중복 호출 방지
 * - refreshTokens 실패 시 자동 로그아웃 — 사용자에게 알림 UI 필요
 * - localStorage 키를 interceptor와 반드시 일치시킬 것
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
