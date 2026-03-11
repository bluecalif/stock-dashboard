import { create } from "zustand";
import type { ChatSession, ChatMessage } from "../types/chat";
import * as chatApi from "../api/chat";

interface ChatState {
  sessions: ChatSession[];
  activeSessionId: string | null;
  messages: ChatMessage[];
  isStreaming: boolean;
  isPanelOpen: boolean;

  // Actions
  togglePanel: () => void;
  openPanel: () => void;
  closePanel: () => void;
  loadSessions: () => Promise<void>;
  createSession: (title?: string) => Promise<ChatSession>;
  selectSession: (sessionId: string) => Promise<void>;
  setStreaming: (v: boolean) => void;
  addUserMessage: (content: string) => void;
  appendAssistantDelta: (content: string) => void;
  finalizeAssistant: () => void;
  clearChat: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  sessions: [],
  activeSessionId: null,
  messages: [],
  isStreaming: false,
  isPanelOpen: false,

  togglePanel: () => set((s) => ({ isPanelOpen: !s.isPanelOpen })),
  openPanel: () => set({ isPanelOpen: true }),
  closePanel: () => set({ isPanelOpen: false }),

  loadSessions: async () => {
    const sessions = await chatApi.listSessions();
    set({ sessions });
  },

  createSession: async (title?: string) => {
    const session = await chatApi.createSession(title);
    set((s) => ({
      sessions: [session, ...s.sessions],
      activeSessionId: session.id,
      messages: [],
    }));
    return session;
  },

  selectSession: async (sessionId: string) => {
    set({ activeSessionId: sessionId, messages: [] });
    const detail = await chatApi.getSession(sessionId);
    set({ messages: detail.messages });
  },

  setStreaming: (v) => set({ isStreaming: v }),

  addUserMessage: (content: string) => {
    const msg: ChatMessage = {
      id: crypto.randomUUID(),
      session_id: get().activeSessionId || "",
      role: "user",
      content,
      tool_payload: null,
      token_count: null,
      created_at: new Date().toISOString(),
    };
    set((s) => ({ messages: [...s.messages, msg] }));
  },

  appendAssistantDelta: (content: string) => {
    set((s) => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === "assistant" && last.id === "__streaming__") {
        // 기존 스트리밍 메시지에 추가
        msgs[msgs.length - 1] = { ...last, content: (last.content || "") + content };
      } else {
        // 새 스트리밍 메시지 생성
        msgs.push({
          id: "__streaming__",
          session_id: s.activeSessionId || "",
          role: "assistant",
          content,
          tool_payload: null,
          token_count: null,
          created_at: new Date().toISOString(),
        });
      }
      return { messages: msgs };
    });
  },

  finalizeAssistant: () => {
    set((s) => {
      const msgs = s.messages.map((m) =>
        m.id === "__streaming__" ? { ...m, id: crypto.randomUUID() } : m,
      );
      return { messages: msgs, isStreaming: false };
    });
  },

  clearChat: () => set({ activeSessionId: null, messages: [] }),
}));
