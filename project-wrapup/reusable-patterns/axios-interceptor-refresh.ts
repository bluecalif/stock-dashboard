/**
 * ## 용도
 * Axios Interceptor — Bearer 자동 주입 + 401 시 Refresh Token 재인증 + 동시 요청 큐.
 * 거의 복붙 가능 (baseURL만 변경).
 *
 * ## 언제 쓰는가
 * JWT 인증 + React 프론트엔드에서 모든 API 요청에 토큰을 자동 주입하고,
 * 401 발생 시 자동으로 refresh → 원래 요청 재시도가 필요할 때.
 *
 * ## 전제조건
 * - JWT 기반 백엔드 (access + refresh token)
 * - localStorage에 auth_tokens 키로 토큰 저장 (zustand-auth-store.ts 참조)
 *
 * ## 의존성
 * - axios: HTTP 클라이언트
 * - import.meta.env.VITE_API_BASE_URL: 백엔드 URL (Vite 환경변수)
 *
 * ## 통합 포인트
 * - api/client.ts에 배치
 * - 모든 API 호출에서 import { default as apiClient } from './client'
 * - zustand-auth-store.ts와 localStorage 키(auth_tokens) 공유
 * - 주의: SSE(fetch API)는 이 interceptor 범위 밖 — 별도 401 처리 필요 (T-014)
 *
 * ## 주의사항
 * - SSE/WebSocket은 axios가 아닌 fetch API 사용 → 이 interceptor 미적용
 * - refresh 엔드포인트 자체는 retry 제외 처리 필수 (무한 루프 방지)
 * - 동시 요청 큐(pendingRequests)는 refresh 완료 후 일괄 처리
 *
 * ## 출처
 * stock-dashboard/frontend/src/api/client.ts
 */

import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
});

let isRefreshing = false;
let pendingRequests: Array<(token: string) => void> = [];

// Request: Bearer 토큰 자동 주입
apiClient.interceptors.request.use((config) => {
  try {
    const raw = localStorage.getItem("auth_tokens");
    if (raw) {
      const { accessToken } = JSON.parse(raw);
      if (accessToken) {
        config.headers.Authorization = `Bearer ${accessToken}`;
      }
    }
  } catch {
    // ignore
  }
  return config;
});

// Response: 401 시 refresh 시도 → 원래 요청 재시도
apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    const originalRequest = error.config;

    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes("/v1/auth/refresh") &&
      !originalRequest.url?.includes("/v1/auth/login")
    ) {
      // 이미 refresh 중이면 큐에 대기
      if (isRefreshing) {
        return new Promise((resolve) => {
          pendingRequests.push((token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            resolve(apiClient(originalRequest));
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const raw = localStorage.getItem("auth_tokens");
        const { refreshToken } = JSON.parse(raw!);
        const res = await apiClient.post("/v1/auth/refresh", {
          refresh_token: refreshToken,
        });

        const newAccessToken = res.data.access_token;
        localStorage.setItem(
          "auth_tokens",
          JSON.stringify({
            accessToken: newAccessToken,
            refreshToken: res.data.refresh_token,
          }),
        );

        // 대기 중인 요청 모두 처리
        pendingRequests.forEach((cb) => cb(newAccessToken));
        pendingRequests = [];

        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch {
        localStorage.removeItem("auth_tokens");
        window.location.href = "/login";
        return Promise.reject(error);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);

export default apiClient;
