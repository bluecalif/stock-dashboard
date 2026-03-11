# Phase B: Chatbot 기본 루프
> Last Updated: 2026-03-12
> Status: Planning

## 1. Summary (개요)

**목적**: LangGraph + Gemini 기반 대화형 분석 챗봇 구축. 사용자가 자연어로 자산/팩터/전략 데이터를 질의하고, SSE 스트리밍으로 실시간 응답을 받는 기본 대화 루프 완성.

**범위**:
- Backend LLM 계층: LangGraph StateGraph (agent→tools 루프), LangChain Tool, 시스템 프롬프트
- Backend Chat: chat_sessions/chat_messages DB, chat_service (SSE 오케스트레이션), chat router
- Frontend Chat: chatStore (Zustand), ChatPanel (슬라이드 패널), SSE 파싱, 메시지 UI
- 기존 API/페이지: 변경 없음 (채팅 패널은 레이아웃 오버레이)

**예상 결과물**:
- 채팅 세션 생성 → 메시지 전송 → LLM이 Tool 호출 → 실시간 텍스트 응답
- Tool: 가격 조회, 팩터 조회, 상관행렬 조회, 시그널 조회, 백테스트 목록
- SSE 이벤트: text_delta, tool_call, tool_result, done
- 우측 슬라이드 채팅 패널 UI

## 2. Current State (현재 상태)

- Phase A Auth 완료 (16/16 tasks)
- JWT 인증 운영 중 (access 30min, refresh 7d, rotation)
- Zustand authStore + ProtectedRoute 구현 완료
- Backend: Router-Service-Repository 3계층, 16 endpoints (12 MVP + 4 Auth)
- Frontend: React 19 + Vite + TypeScript + Tailwind + zustand + axios
- Railway (backend+DB) + Vercel (frontend) 운영 중
- Tests: 426 passed, ruff clean

## 3. Target State (목표 상태)

| 영역 | Before | After |
|------|--------|-------|
| DB | 10 테이블 | 12 테이블 (+chat_sessions, chat_messages) |
| API | 16 endpoints | 19 endpoints (+3 chat) |
| Backend 서비스 | auth_service | + chat_service, LLM graph/tools/prompts |
| Frontend 상태 | authStore | + chatStore |
| Frontend UI | 6 pages + login/signup | + ChatPanel (슬라이드 패널) |
| 외부 의존 | - | Google Gemini API (langgraph, langchain) |
| 설정 | JWT 설정 | + google_api_key, gemini model 설정 |

## 4. Implementation Stages

### Stage A: Backend LLM 기반 (Step B.1~B.4)
- Settings 확장 (google_api_key, gemini model names)
- LangGraph StateGraph 정의 (agent→tools→agent 루프)
- LangChain Tool 정의 (기존 DB 데이터 조회)
- 시스템 프롬프트 템플릿

### Stage B: Backend Chat 데이터 (Step B.5~B.7)
- chat_sessions, chat_messages DB 모델 + Alembic 마이그레이션
- Chat 스키마 (세션/메시지 요청·응답)
- Chat Repository (세션 CRUD, 메시지 저장/조회)

### Stage C: Backend Chat API (Step B.8~B.10)
- Chat Service (LangGraph astream_events → SSE 오케스트레이션)
- Chat Router (POST sessions, GET session, POST messages → SSE)
- main.py 라우터 등록 + pyproject.toml 의존성

### Stage D: Backend 테스트 (Step B.11~B.12)
- Chat 단위 테스트 (service mock, router, schema)
- Regression: 기존 tests 통과 확인

### Stage E: Frontend Chat (Step B.13~B.17)
- Chat 타입 + API 함수
- useSSE hook (fetch + ReadableStream, POST 지원)
- chatStore (Zustand: sessions, messages, streaming state)
- ChatPanel + MessageBubble + ChatInput 컴포넌트
- Layout에 ChatPanel 통합 (토글 버튼)

### Stage F: E2E 검증 + 문서 (Step B.18~B.19)
- E2E 검증 (로그인 → 채팅 → Tool 호출 → 스트리밍 응답)
- dev-docs 갱신

## 5. Task Breakdown

| Step | Task | Size | Depends | Stage |
|------|------|------|---------|-------|
| B.1 | Settings: google_api_key, gemini_pro_model, gemini_lite_model | S | - | A |
| B.2 | LangGraph graph.py: StateGraph (agent→tools→agent 루프) | L | B.1 | A |
| B.3 | LangChain tools.py: prices, factors, correlation, signals, backtests | M | B.2 | A |
| B.4 | prompts.py: 시스템 프롬프트 (한국어, 분석 도우미 역할) | S | B.2 | A |
| B.5 | DB 모델: chat_sessions, chat_messages + Alembic migration | M | - | B |
| B.6 | Pydantic 스키마: chat.py (Session/Message 요청·응답) | S | B.5 | B |
| B.7 | Repository: chat_repo.py (세션 CRUD, 메시지 저장/조회) | M | B.5 | B |
| B.8 | Service: chat_service.py (LangGraph → SSE 오케스트레이션) | L | B.2, B.7 | C |
| B.9 | Router: chat.py (POST sessions, GET session, POST messages SSE) | M | B.6, B.8 | C |
| B.10 | main.py 라우터 등록 + pyproject.toml 의존성 추가 | S | B.9 | C |
| B.11 | 단위 테스트: chat service (LLM mock) + chat router | M | B.9 | D |
| B.12 | Regression: 기존 tests 통과 확인 + ruff | S | B.10 | D |
| B.13 | Frontend: types/chat.ts + api/chat.ts | S | B.9 | E |
| B.14 | Frontend: hooks/useSSE.ts (fetch + ReadableStream POST SSE) | M | B.13 | E |
| B.15 | Frontend: store/chatStore.ts (sessions, messages, streaming) | M | B.13 | E |
| B.16 | Frontend: ChatPanel + MessageBubble + ChatInput 컴포넌트 | L | B.14, B.15 | E |
| B.17 | Frontend: Layout에 ChatPanel 통합 (토글 버튼 + 슬라이드) | S | B.16 | E |
| B.18 | E2E 검증: 로그인 → 채팅 → Tool 호출 → 스트리밍 응답 | M | B.12, B.17 | F |
| B.19 | dev-docs 갱신 + 커밋 | S | B.18 | F |

**Size 분포**: S: 7, M: 7, L: 3, XL: 0 — **총 19 tasks** (추정 파일: 신규 18 / 수정 5 / Migration 1)

## 6. Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Gemini API 키 미발급/할당량 부족 | 챗봇 전체 불능 | 중 | Phase 착수 전 키 발급 확인, 무료 티어 한도 파악 |
| LangGraph SSE 이벤트 포맷 불일치 | 프론트 파싱 오류 | 중 | astream_events v2 사용, 이벤트 타입 필터링 |
| Tool 호출 시 DB 커넥션 관리 | 세션 누수 | 중 | Tool 내 별도 세션 관리 (context manager) |
| LLM 응답 지연 (>10s) | UX 저하 | 중 | SSE 스트리밍으로 체감 지연 감소, timeout 설정 |
| LLM 할루시네이션 (잘못된 데이터 해석) | 사용자 오해 | 중 | Tool 결과 기반 응답 강제, 시스템 프롬프트 제약 |
| Railway 환경에서 langgraph 의존성 크기 | 배포 시간 증가 | 저 | requirements 최소화 |
| EventSource(GET) 사용 시 POST 미지원 | SSE 구현 실패 | 중 | fetch + ReadableStream 사용 (GET EventSource 금지) |

## 7. Dependencies

### 내부 (기존 모듈)
- `db/models.py` — Base 상속, 기존 패턴 따름
- `db/session.py` — SessionLocal
- `api/dependencies.py` — get_db, get_current_user
- `api/main.py` — 라우터 등록
- `config/settings.py` — Settings 확장
- `api/repositories/*_repo.py` — Tool에서 기존 repo 함수 호출
- `api/services/correlation_service.py` — Tool에서 상관행렬 호출

### 외부 (신규 라이브러리)
- `langgraph` — 그래프 엔진
- `langchain-core` — Tool, PromptTemplate, Message 타입
- `langchain-google-genai` — ChatGoogleGenerativeAI (Gemini)
- `google-generativeai` — Gemini SDK (langchain-google-genai 의존)

### 환경변수 (신규)
- `GOOGLE_API_KEY` — Gemini API 키
- `GEMINI_PRO_MODEL` — 메인 모델 (기본: gemini-3.1-pro-preview)
- `GEMINI_LITE_MODEL` — 경량 모델 (기본: gemini-3.1-flash-lite-preview)
