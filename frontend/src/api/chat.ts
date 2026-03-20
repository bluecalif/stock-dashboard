import apiClient from "./client";
import type { ChatSession, SessionDetailResponse } from "../types/chat";

export async function createSession(title?: string): Promise<ChatSession> {
  const res = await apiClient.post<ChatSession>("/v1/chat/sessions", { title });
  return res.data;
}

export async function listSessions(): Promise<ChatSession[]> {
  const res = await apiClient.get<ChatSession[]>("/v1/chat/sessions");
  return res.data;
}

export async function getSession(sessionId: string): Promise<SessionDetailResponse> {
  const res = await apiClient.get<SessionDetailResponse>(
    `/v1/chat/sessions/${sessionId}`,
  );
  return res.data;
}

/**
 * SSE 메시지 전송 — fetch + ReadableStream (POST 지원).
 * EventSource는 GET만 지원하므로 사용하지 않음.
 */
export interface PageContext {
  page_id: string;
  asset_ids: string[];
  params: Record<string, unknown>;
}

export function sendMessageSSE(
  sessionId: string,
  content: string,
  accessToken: string | null,
  deepMode: boolean = false,
  pageContext?: PageContext,
  isNudge: boolean = false,
): { response: Promise<Response>; abort: () => void } {
  const controller = new AbortController();
  const baseURL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

  const doFetch = (token: string | null) =>
    fetch(`${baseURL}/v1/chat/sessions/${sessionId}/messages`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        content,
        deep_mode: deepMode,
        page_context: pageContext ?? null,
        is_nudge: isNudge,
      }),
      signal: controller.signal,
    });

  // 401 시 토큰 갱신 후 1회 재시도
  const response = doFetch(accessToken).then(async (res) => {
    if (res.status !== 401) return res;

    try {
      const raw = localStorage.getItem("auth_tokens");
      if (!raw) return res;
      const { refreshToken } = JSON.parse(raw);

      const refreshRes = await apiClient.post("/v1/auth/refresh", {
        refresh_token: refreshToken,
      });

      const newAccessToken = refreshRes.data.access_token;
      const newRefreshToken = refreshRes.data.refresh_token;

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

      return doFetch(newAccessToken);
    } catch {
      return res; // refresh 실패 시 원래 401 응답 반환
    }
  });

  return { response, abort: () => controller.abort() };
}

export async function fetchNudgeQuestions(pageId: string): Promise<string[]> {
  const res = await apiClient.get<{ questions: string[] }>(
    "/v1/chat/nudge-questions",
    { params: { page_id: pageId } },
  );
  return res.data.questions;
}
