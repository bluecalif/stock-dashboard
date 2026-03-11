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
  type: "text_delta" | "tool_call" | "tool_result" | "done" | "error";
  content?: string;
  name?: string;
  args?: Record<string, unknown>;
  data?: unknown;
}
