# Phase B: Chatbot — Tasks
> Last Updated: 2026-03-12
> Status: Planning (0/19)

## Stage A: Backend LLM 기반 (Step B.1~B.4)

- [ ] B.1 Settings: google_api_key, gemini_pro_model, gemini_lite_model `[S]`
  - `config/settings.py` 확장
  - `.env.example` 업데이트
  - 로컬 `.env`에 GOOGLE_API_KEY 추가

- [ ] B.2 LangGraph graph.py: StateGraph (agent→tools→agent 루프) `[L]`
  - `api/services/llm/graph.py` 신규
  - MessagesState, agent_node, route_tools, ToolNode
  - MemorySaver checkpointer (dev)

- [ ] B.3 LangChain tools.py: 5개 Tool 정의 `[M]`
  - `api/services/llm/tools.py` 신규
  - get_prices, get_factors, get_correlation, get_signals, list_backtests
  - 각 Tool: 별도 DB 세션 → repo 함수 호출 → JSON 문자열 반환

- [ ] B.4 prompts.py: 시스템 프롬프트 `[S]`
  - `api/services/llm/prompts.py` 신규
  - 한국어 분석 도우미 역할
  - 데이터 근거 기반 응답 강제, 할루시네이션 방지 지시

## Stage B: Backend Chat 데이터 (Step B.5~B.7)

- [ ] B.5 DB 모델: ChatSession, ChatMessage + Alembic migration `[M]`
  - `db/models.py`에 모델 추가
  - `alembic revision --autogenerate -m "Add chat tables"`
  - Railway DB에 마이그레이션 적용

- [ ] B.6 Pydantic 스키마: chat.py `[S]`
  - CreateSessionRequest, SessionResponse, MessageListResponse
  - SendMessageRequest, MessageResponse
  - SSEEvent (text_delta, tool_call, tool_result, done)

- [ ] B.7 Repository: chat_repo.py `[M]`
  - create_session, get_session, list_sessions_by_user
  - create_message, list_messages_by_session

## Stage C: Backend Chat API (Step B.8~B.10)

- [ ] B.8 Service: chat_service.py (LangGraph → SSE 오케스트레이션) `[L]`
  - astream_events() 호출 → SSE 이벤트 변환
  - user/assistant 메시지 DB 저장
  - 에러 핸들링 (LLM timeout, API 오류)

- [ ] B.9 Router: chat.py (3 endpoints) `[M]`
  - POST `/v1/chat/sessions` → SessionResponse
  - GET `/v1/chat/sessions/{session_id}` → SessionResponse + messages
  - POST `/v1/chat/sessions/{session_id}/messages` → StreamingResponse (SSE)

- [ ] B.10 main.py 라우터 등록 + pyproject.toml 의존성 `[S]`
  - `app.include_router(chat.router)`
  - langgraph, langchain-core, langchain-google-genai 추가

## Stage D: Backend 테스트 (Step B.11~B.12)

- [ ] B.11 단위 테스트: chat service (LLM mock) + chat router `[M]`
  - test_chat_service.py: LLM mock, 세션 생성, 메시지 저장
  - test_chat_router.py: httpx TestClient 엔드포인트 테스트

- [ ] B.12 Regression: 기존 tests 통과 + ruff `[S]`
  - `python -m pytest` 전체 실행
  - `ruff check .` lint 통과

## Stage E: Frontend Chat (Step B.13~B.17)

- [ ] B.13 Frontend: types/chat.ts + api/chat.ts `[S]`
  - ChatSession, ChatMessage, SSEEvent 타입
  - createSession, getSession, sendMessage API 함수

- [ ] B.14 Frontend: hooks/useSSE.ts `[M]`
  - fetch + ReadableStream SSE 파싱
  - POST 메서드 지원 (EventSource 대신)
  - onTextDelta, onToolCall, onToolResult, onDone 콜백

- [ ] B.15 Frontend: store/chatStore.ts `[M]`
  - sessions, activeSessionId, messages, isStreaming
  - createSession, sendMessage, appendMessage actions

- [ ] B.16 Frontend: ChatPanel + MessageBubble + ChatInput `[L]`
  - ChatPanel: 우측 슬라이드 패널 (w-96)
  - MessageBubble: user(우측)/assistant(좌측)/tool(축소) 구분
  - ChatInput: 텍스트 입력 + 전송 버튼 + 스트리밍 중 비활성

- [ ] B.17 Frontend: Layout에 ChatPanel 통합 `[S]`
  - Layout.tsx에 채팅 토글 버튼 추가
  - ChatPanel 오버레이 (기존 레이아웃 유지)

## Stage F: E2E 검증 + 문서 (Step B.18~B.19)

- [ ] B.18 E2E 검증 `[M]`
  - 로그인 → 채팅 세션 생성 → 메시지 전송 → SSE 응답 수신
  - Tool 호출 확인 (가격/팩터/상관 질의)
  - 세션 재접속 → 대화 이력 복원
  - 기존 대시보드 페이지 정상 동작 확인

- [ ] B.19 dev-docs 갱신 + 커밋 `[S]`
  - Phase B tasks 업데이트 (commit hash 기록)
  - project-overall 동기화
  - session-compact 갱신

---

## Summary
- **Total**: 19 tasks (S: 7, M: 7, L: 3)
- **Progress**: 0/19 (0%)
- **파일 집계**: 신규 18 / 수정 5 / Migration 1
