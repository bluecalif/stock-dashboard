import { useEffect, useRef, useCallback } from "react";
import { useLocation } from "react-router-dom";
import { useChatStore } from "../../store/chatStore";
import { useAuthStore } from "../../store/authStore";
import { useChartActionStore } from "../../store/chartActionStore";
import { sendMessageSSE } from "../../api/chat";
import type { PageContext } from "../../api/chat";
import type { UIAction } from "../../types/chat";
import { useSSE } from "../../hooks/useSSE";
import MessageBubble from "./MessageBubble";
import ChatInput from "./ChatInput";

export default function ChatPanel() {
  const {
    isPanelOpen,
    closePanel,
    activeSessionId,
    messages,
    isStreaming,
    sessions,
    deepMode,
    toggleDeepMode,
    loadSessions,
    createSession,
    selectSession,
    setStreaming,
    addUserMessage,
    appendAssistantDelta,
    finalizeAssistant,
  } = useChatStore();

  const accessToken = useAuthStore((s) => s.accessToken);
  const { push: pushAction, setHighlightedPair, setFilter } = useChartActionStore();
  const { startStream } = useSSE();
  const location = useLocation();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  /** 현재 페이지 경로에서 page_id 추출 */
  const getPageContext = useCallback((): PageContext => {
    const path = location.pathname.replace(/^\//, "") || "home";
    return { page_id: path, asset_ids: [], params: {} };
  }, [location.pathname]);

  /** SSE ui_action 이벤트 처리 */
  const handleUIAction = useCallback(
    (action: UIAction) => {
      switch (action.action) {
        case "highlight_pair":
          setHighlightedPair({
            asset_a: action.payload.asset_a as string,
            asset_b: action.payload.asset_b as string,
          });
          break;
        case "set_filter":
          setFilter(
            action.payload.key as string,
            action.payload.value as string | string[],
          );
          break;
        default:
          pushAction(action);
          break;
      }
    },
    [pushAction, setHighlightedPair, setFilter],
  );

  // 패널 열릴 때 세션 목록 로드
  useEffect(() => {
    if (isPanelOpen) {
      loadSessions();
    }
  }, [isPanelOpen, loadSessions]);

  // 메시지 추가 시 스크롤
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = useCallback(
    async (content: string) => {
      let sessionId = activeSessionId;

      // 세션 없으면 자동 생성
      if (!sessionId) {
        const session = await createSession(content.slice(0, 50));
        sessionId = session.id;
      }

      addUserMessage(content);
      setStreaming(true);

      const pageContext = getPageContext();
      const { response, abort } = sendMessageSSE(
        sessionId, content, accessToken, deepMode, pageContext,
      );

      await startStream(response, abort, {
        onTextDelta: (text) => appendAssistantDelta(text),
        onUIAction: handleUIAction,
        onDone: () => finalizeAssistant(),
        onError: (msg) => {
          appendAssistantDelta(`\n\n⚠️ 오류: ${msg}`);
          finalizeAssistant();
        },
      });
    },
    [
      activeSessionId,
      accessToken,
      deepMode,
      createSession,
      addUserMessage,
      setStreaming,
      startStream,
      appendAssistantDelta,
      finalizeAssistant,
      getPageContext,
      handleUIAction,
    ],
  );

  if (!isPanelOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white shadow-xl border-l border-gray-200 flex flex-col z-50">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50">
        <h2 className="font-semibold text-gray-800">AI 분석 도우미</h2>
        <button
          onClick={closePanel}
          className="text-gray-400 hover:text-gray-600 text-xl leading-none"
        >
          ✕
        </button>
      </div>

      {/* Session selector (간단) */}
      {!activeSessionId && sessions.length > 0 && (
        <div className="border-b border-gray-100 px-4 py-2 max-h-40 overflow-y-auto">
          <p className="text-xs text-gray-400 mb-1">이전 대화</p>
          {sessions.slice(0, 5).map((s) => (
            <button
              key={s.id}
              onClick={() => selectSession(s.id)}
              className="block w-full text-left text-sm text-gray-600 hover:bg-gray-100 rounded px-2 py-1 truncate"
            >
              {s.title || "새 대화"}
            </button>
          ))}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto py-3">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-gray-400 text-sm">
            질문을 입력하면 데이터를 분석해 드립니다
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput onSend={handleSend} disabled={isStreaming} deepMode={deepMode} onToggleDeepMode={toggleDeepMode} />
    </div>
  );
}
