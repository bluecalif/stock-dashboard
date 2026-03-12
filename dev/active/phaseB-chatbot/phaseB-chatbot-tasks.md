# Phase B: Chatbot — Tasks
> Last Updated: 2026-03-12
> Status: Complete (19/19)

## Stage A: Backend LLM 기반 (Step B.1~B.4)

- [x] B.1 Settings: openai_api_key, llm_pro_model, llm_lite_model `[S]` — `936bc9a`, `807c33f`
  - `config/settings.py` 확장 (Gemini → OpenAI 전환)
  - `.env.example` 업데이트
  - 로컬 `.env`에 OPENAI_API_KEY 추가

- [x] B.2 LangGraph graph.py: StateGraph (agent→tools→agent 루프) `[L]` — `936bc9a`, `807c33f`
  - `api/services/llm/graph.py` 신규
  - MessagesState, agent_node, route_tools, ToolNode
  - MemorySaver checkpointer (dev)
  - deep_mode 파라미터로 모델 선택 (lite/pro) — `2202455`

- [x] B.3 LangChain tools.py: 5개 Tool 정의 `[M]` — `936bc9a`
  - `api/services/llm/tools.py` 신규
  - get_prices, get_factors, get_correlation, get_signals, list_backtests
  - 각 Tool: 별도 DB 세션 → repo 함수 호출 → JSON 문자열 반환

- [x] B.4 prompts.py: 시스템 프롬프트 `[S]` — `936bc9a`
  - `api/services/llm/prompts.py` 신규
  - 한국어 분석 도우미 역할
  - 데이터 근거 기반 응답 강제, 할루시네이션 방지 지시

## Stage B: Backend Chat 데이터 (Step B.5~B.7)

- [x] B.5 DB 모델: ChatSession, ChatMessage + Alembic migration `[M]` — `e73096a`
  - `db/models.py`에 모델 추가
  - Alembic migration 생성 + Railway DB 적용

- [x] B.6 Pydantic 스키마: chat.py `[S]` — `e73096a`
  - CreateSessionRequest, SessionResponse, MessageListResponse
  - SendMessageRequest (+ deep_mode 추가 `2202455`), MessageResponse
  - SSEEvent (text_delta, tool_call, tool_result, done)

- [x] B.7 Repository: chat_repo.py `[M]` — `e73096a`
  - create_session, get_session, list_sessions_by_user
  - create_message, list_messages_by_session

## Stage C: Backend Chat API (Step B.8~B.10)

- [x] B.8 Service: chat_service.py (LangGraph → SSE 오케스트레이션) `[L]` — `fa112e6`
  - astream_events() 호출 → SSE 이벤트 변환
  - user/assistant 메시지 DB 저장
  - 에러 핸들링 (LLM timeout, API 오류)
  - ToolMessage 직렬화 수정 — `689dedf`
  - deep_mode 파라미터 전달 — `2202455`

- [x] B.9 Router: chat.py (4 endpoints) `[M]` — `fa112e6`
  - POST `/v1/chat/sessions` → SessionResponse
  - GET `/v1/chat/sessions` → 세션 목록
  - GET `/v1/chat/sessions/{session_id}` → SessionResponse + messages
  - POST `/v1/chat/sessions/{session_id}/messages` → StreamingResponse (SSE)

- [x] B.10 main.py 라우터 등록 + pyproject.toml 의존성 `[S]` — `fa112e6`, `807c33f`
  - `app.include_router(chat.router)`
  - langchain-openai 추가 (langchain-google-genai → langchain-openai 전환)

## Stage D: Backend 테스트 (Step B.11~B.12)

- [x] B.11 단위 테스트: chat service (LLM mock) + chat router `[M]` — `3d8dcd7`
  - test_chat_service.py: LLM mock, 세션 생성, 메시지 저장
  - test_chat_router.py: httpx TestClient 엔드포인트 테스트

- [x] B.12 Regression: 기존 tests 통과 + ruff `[S]` — `3d8dcd7`
  - `python -m pytest` 전체 실행: 440 passed
  - `ruff check .` lint 통과

## Stage E: Frontend Chat (Step B.13~B.17)

- [x] B.13 Frontend: types/chat.ts + api/chat.ts `[S]` — `5db4127`
  - ChatSession, ChatMessage, SSEEvent 타입
  - createSession, getSession, sendMessage API 함수
  - deep_mode 파라미터 추가 — `2202455`

- [x] B.14 Frontend: hooks/useSSE.ts `[M]` — `5db4127`
  - fetch + ReadableStream SSE 파싱
  - POST 메서드 지원 (EventSource 대신)
  - onTextDelta, onToolCall, onToolResult, onDone 콜백

- [x] B.15 Frontend: store/chatStore.ts `[M]` — `5db4127`
  - sessions, activeSessionId, messages, isStreaming
  - deepMode + toggleDeepMode 추가 — `2202455`

- [x] B.16 Frontend: ChatPanel + MessageBubble + ChatInput `[L]` — `5db4127`
  - ChatPanel: 우측 슬라이드 패널 (w-96)
  - MessageBubble: user(우측)/assistant(좌측)/tool(축소) 구분
  - ChatInput: 텍스트 입력 + 전송 버튼 + 심층모드 토글 — `2202455`

- [x] B.17 Frontend: Layout에 ChatPanel 통합 `[S]` — `5db4127`
  - Layout.tsx에 채팅 토글 버튼 추가 (💬)
  - ChatPanel 오버레이 (기존 레이아웃 유지)
  - TS 빌드 에러 수정 (unused stopStream) — `2f21d0d`

## Stage F: E2E 검증 + 문서 (Step B.18~B.19)

- [x] B.18 E2E 검증 `[M]` — `807c33f`, `689dedf`, `2f21d0d`
  - LLM Gemini → OpenAI GPT-5 전환 (graph.py, settings, pyproject.toml)
  - langchain-openai 1.1.11, langgraph 1.1.1, langchain-core 1.2.18
  - ToolMessage JSON 직렬화 버그 수정
  - 로컬 E2E: 로그인 → 세션 생성 → Tool 호출 → SSE 스트리밍 ✅
  - 프로덕션 E2E: Railway + Vercel 정상 동작 ✅
  - Railway 환경변수: OPENAI_API_KEY (book-process) 설정 완료

- [x] B.19 dev-docs 갱신 + 심층모드 + 커밋 `[S]` — `2202455`
  - 심층모드 토글: 기본 GPT-5 Mini, 토글 시 GPT-5
  - Phase B tasks 업데이트 (commit hash 기록)
  - project-overall 동기화
  - session-compact 갱신

---

## Summary
- **Total**: 19 tasks (S: 7, M: 7, L: 3)
- **Progress**: 19/19 (100%) ✅
- **파일 집계**: 신규 18 / 수정 8 / Migration 1
