/**
 * ## 용도
 * Axios Request/Response Interceptor — Bearer 토큰 자동 주입 + 401 시 Refresh Token으로 재인증.
 * 동시 요청 시 중복 refresh 방지 (큐 패턴).
 *
 * ## 사용법
 * 1. apiClient 생성 (baseURL 설정)
 * 2. localStorage에 auth_tokens 저장 (saveTokens 함수)
 * 3. import해서 사용 — apiClient.get/post/put/delete
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
