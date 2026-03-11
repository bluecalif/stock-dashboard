import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
});

// Request interceptor — attach Bearer token
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
    // ignore parse errors
  }
  return config;
});

// Response interceptor — 401 시 refresh 시도
let isRefreshing = false;
let pendingRequests: Array<(token: string) => void> = [];

apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    const originalRequest = error.config;

    // 401이고 refresh 엔드포인트가 아닌 경우에만 retry
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes("/v1/auth/refresh") &&
      !originalRequest.url?.includes("/v1/auth/login")
    ) {
      if (isRefreshing) {
        // 이미 refresh 중이면 대기열에 추가
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
        if (!raw) throw new Error("No tokens");
        const { refreshToken } = JSON.parse(raw);

        const res = await apiClient.post("/v1/auth/refresh", {
          refresh_token: refreshToken,
        });

        const newAccessToken = res.data.access_token;
        const newRefreshToken = res.data.refresh_token;

        localStorage.setItem(
          "auth_tokens",
          JSON.stringify({ accessToken: newAccessToken, refreshToken: newRefreshToken }),
        );

        // zustand store 동기화
        const { useAuthStore } = await import("../store/authStore");
        useAuthStore.setState({
          accessToken: newAccessToken,
          refreshToken: newRefreshToken,
        });

        // 대기 중인 요청들 처리
        pendingRequests.forEach((cb) => cb(newAccessToken));
        pendingRequests = [];

        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch {
        // refresh 실패 → 로그아웃
        localStorage.removeItem("auth_tokens");
        const { useAuthStore } = await import("../store/authStore");
        useAuthStore.setState({ user: null, accessToken: null, refreshToken: null });
        window.location.href = "/login";
        return Promise.reject(error);
      } finally {
        isRefreshing = false;
      }
    }

    const msg =
      error.response?.data?.detail || error.message || "Unknown error";
    console.error(`[API] ${error.config?.method?.toUpperCase()} ${error.config?.url} → ${msg}`);
    return Promise.reject(error);
  },
);

export default apiClient;
