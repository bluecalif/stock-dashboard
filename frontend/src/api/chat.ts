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
export function sendMessageSSE(
  sessionId: string,
  content: string,
  accessToken: string | null,
): { response: Promise<Response>; abort: () => void } {
  const controller = new AbortController();
  const baseURL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

  const response = fetch(
    `${baseURL}/v1/chat/sessions/${sessionId}/messages`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      },
      body: JSON.stringify({ content }),
      signal: controller.signal,
    },
  );

  return { response, abort: () => controller.abort() };
}
