export interface ChatSession {
  id: string;
  user_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: "user" | "assistant" | "tool";
  content: string | null;
  tool_payload: Record<string, unknown> | null;
  token_count: number | null;
  created_at: string;
}

export interface SessionDetailResponse extends ChatSession {
  messages: ChatMessage[];
}

export interface SSEEvent {
  type: "text_delta" | "tool_call" | "tool_result" | "ui_action" | "done" | "error";
  content?: string;
  name?: string;
  args?: Record<string, unknown>;
  data?: unknown;
  action?: string;
  payload?: Record<string, unknown>;
}

/** Backend에서 SSE로 전송하는 UI 액션 타입 */
export interface UIAction {
  action: "navigate" | "update_chart" | "set_filter" | "highlight_pair";
  payload: Record<string, unknown>;
}
