# Project Overall Plan
> Last Updated: 2026-03-11
> Status: MVP 완료 (Phase 0~7), Post-MVP 기획 완료 (Phase A~F 계획)

## 1. Summary (개요)

**목적**: 7개 자산(KOSPI200, 삼성전자, SK하이닉스, SOXL, BTC, Gold, Silver)의 일봉 데이터 수집/저장/분석/시각화 MVP → **대화형 분석 워크스페이스**로 확장.

**범위**:
- **MVP (완료)**: Phase 0~7 — 수집 → 분석 → API → 대시보드 → 배포 → 자동 수집
- **Post-MVP (계획)**: Phase A~F — 인증 → 챗봇 → 분석 시나리오 → 메모리/벡터 → 차트 커스텀 → 온보딩

**MVP 결과물**:
- FDR 기반 일봉 수집 파이프라인 ✅
- PostgreSQL 데이터 저장소 (Railway) ✅
- 팩터/전략/백테스트 분석 엔진 ✅
- FastAPI 조회/백테스트/집계 API (12개 엔드포인트) ✅
- React + Recharts 대시보드 SPA (6개 페이지) ✅
- GitHub Actions cron 일일 자동 수집 ✅

**Post-MVP 목표 결과물**:
- JWT 인증 + 사용자 컨텍스트
- LangGraph + Gemini 기반 챗봇 (SSE 스트리밍)
- 상관/지표/전략 분석 시나리오 API
- 사용자 메모리 + pgvector 보조 검색
- 차트 커스터마이징 (대화 ↔ 차트 연동)
- 온보딩 에이전트

## 2. Current State (현재 상태)

- **MVP Phase 0~7**: 83/83 tasks 완료
- **Phase 1~3**: 골격 + 수집 + 분석 엔진
- **Phase 4**: FastAPI 12 endpoints, 405 tests
- **Phase 5**: React SPA 6페이지, UX 검증 완료
- **Phase 6**: CI/CD + Railway + Vercel 배포
- **Phase 7**: GitHub Actions cron 일일 자동 수집 (6/6 완료)
- **Post-MVP 기획**: 기술 결정 + 6 Phase 계획 완료
- **Git**: `master` 브랜치, 409 passed + 7 skipped, ruff clean
- **DB**: price_daily 5,573+ rows, factor_daily 55K+, signal_daily 15K+, backtest 21 runs
- **인프라**: Railway (backend+DB), Vercel (frontend), GitHub Actions (CI/CD + cron)

## 3. Target State (목표 상태)

| 영역 | 목표 | 현재 |
|------|------|------|
| 수집 | 7개 자산 일봉 자동 수집, UPSERT, 정합성 검증 | ✅ 완료 |
| DB | 8개 테이블 운영, Alembic 마이그레이션 관리 | ✅ 완료 |
| 분석 | 팩터 15종, 전략 3종, 백테스트 실행 가능 | ✅ 완료 |
| API | 12개 엔드포인트 운영 (조회/백테스트/집계) | ✅ 완료 |
| 대시보드 | 6개 페이지 (홈/가격/상관/팩터/시그널/전략성과) | ✅ 완료 |
| 운영 | 일일 배치, 실패 알림, JSON 로그, 배포 | ✅ 완료 |
| 자동 수집 | GitHub Actions cron 기반 일일 자동 수집 | ✅ 완료 |
| **인증** | JWT 인증, 사용자별 데이터 격리 | ⬜ Phase A |
| **챗봇** | LangGraph + Gemini 대화형 분석 | ⬜ Phase B |
| **분석 시나리오** | 상관 설명, 지표 해석, 전략 비교 API | ⬜ Phase C |
| **차트 커스텀** | 대화 → 차트 반영, preset 저장, 페이지 재편 | ⬜ Phase D |
| **메모리/검색** | 사용자 메모리 + pgvector 보조 검색 | ⬜ Phase E |
| **온보딩** | 관심 자산/전략/알림 수집, 가이드 | ⬜ Phase F |

## 4. Implementation Phases (구현 단계)

### MVP Phases (Phase 0~7) — ✅ 모두 완료

#### Phase 0: 사전 준비 ✅
- 마스터플랜, 데이터 검증, CLAUDE.md 설정, Git 초기화

#### Phase 1: 프로젝트 골격 + DB ✅ (9 tasks)
- Python 프로젝트 초기화, DB 8 테이블, Alembic, asset_master 시드

#### Phase 2: 수집기 (Collector) ✅ (10 tasks)
- FDR 래퍼, UPSERT, 정합성 검증, Discord 알림, 3년 백필 (5,559 rows)

#### Phase 3: 분석 엔진 (Research Engine) ✅ (12 tasks)
- 전처리, 팩터 15개, 전략 3종, 백테스트, 성과지표, 배치 스크립트

#### Phase 4: API ✅ (15 tasks)
> dev-docs: `dev/active/phase4-api/`
- FastAPI 12 endpoints, Router-Service-Repository 3계층, 405 tests

#### Phase 5: 프론트엔드 ✅ (13 tasks)
> dev-docs: `dev/active/phase5-frontend/`
- React SPA 6페이지, Recharts, UX 버그 11개 수정

#### Phase 6: 배포 & 운영 ✅ (9 tasks)
> dev-docs: `dev/active/phase6-deploy/`
- CI/CD + Railway + Vercel + CORS + E2E 검증

#### Phase 7: 스케줄 자동 수집 ✅ (6 tasks)
> dev-docs: `dev/active/phase7-scheduler/`
- GitHub Actions cron (KST 18:00), Railway Public Networking, E2E 검증

---

### Post-MVP Phases (Phase A~F) — 계획 완료

> 참조: `docs/post-mvp-implementation-sketch.md` (제품 요구사항)
> 플랜: `.claude/plans/snuggly-growing-willow.md` (전체 구현 계획)

**구현 순서**: `A (Auth) → B (Chat) → C (Analysis) → D (Graph Custom) → E (Memory+Vector) → F (Onboarding)`
**세부 기획 원칙**: Phase A, B는 상세 확정. Phase C~F는 각 Phase 진입 시 `/dev-docs`로 상세 기획 후 구현.

#### Phase A: Auth + 사용자 컨텍스트 — ⬜ 미시작 (다음 착수) [상세 확정]
> dev-docs: `dev/active/phaseA-auth/`

**목적**: JWT 인증 + 사용자별 데이터 격리 기반 마련
**Stages**: A(Backend 기반) → B(Auth 로직) → C(통합+테스트) → D(Frontend) → E(E2E+문서)
**Tasks**: 16개 (S:6, M:9, L:1)

**Backend 산출물**:
- `users`, `user_sessions` DB 테이블 + Alembic 마이그레이션
- `api/schemas/auth.py` — SignupRequest, LoginRequest, TokenResponse, UserResponse
- `api/repositories/user_repo.py`, `session_repo.py`
- `api/services/auth_service.py` — signup, login, refresh, JWT 생성/검증
- `api/routers/auth.py` — POST signup/login/refresh, GET me
- `config/settings.py` 수정 — jwt_secret_key, jwt_algorithm, access/refresh TTL
- `api/dependencies.py` 수정 — `get_current_user`, `get_current_user_optional`

**Frontend 산출물**:
- `src/store/authStore.ts` — Zustand: user, tokens, login/logout/refresh
- `src/pages/LoginPage.tsx`, `SignupPage.tsx`
- `src/components/auth/ProtectedRoute.tsx`
- `src/api/auth.ts`, `src/types/auth.ts`
- `src/api/client.ts` 수정 — Bearer 자동 첨부, 401시 refresh
- `src/App.tsx` 수정 — /login, /signup 라우트

**토큰 플로우**: Login → access(30분) + refresh(7일) → Bearer 헤더 → get_current_user DI
**기존 API**: auth 없이 접근 가능 유지 (optional auth)
**기술 결정**: python-jose + passlib (JWT 자체 구현)
**파일 집계**: 신규 14 / 수정 6 / Migration 1

#### Phase B: Chatbot 기본 루프 — ⬜ 미시작 [상세 확정]

**목적**: LangGraph + Gemini 기반 대화형 분석 루프

**Backend — LangGraph 계층**:
- `api/services/llm/graph.py` — StateGraph (agent→tools→agent 루프, 조건 엣지)
- `api/services/llm/tools.py` — LangChain Tool (prices, factors, correlation 등)
- `api/services/llm/prompts.py` — ChatPromptTemplate 시스템 프롬프트

**Backend — Chat**:
- `chat_sessions`, `chat_messages` DB 테이블 + Migration
- `api/services/chat/chat_service.py` — LangGraph astream_events() + SSE 오케스트레이션
- `api/schemas/chat.py`, `api/repositories/chat_repo.py`, `api/routers/chat.py`

**SSE 이벤트**: text_delta, tool_call, tool_result, ui_action, done

**Frontend — Chat UI**:
- `src/store/chatStore.ts` — sessions, messages, streaming state
- `src/components/chat/ChatPanel.tsx` — 우측 슬라이드 채팅 패널
- `src/components/chat/MessageBubble.tsx`, `ChatInput.tsx`
- `src/hooks/useSSE.ts` — fetch + ReadableStream SSE 파싱 (POST 지원)
- `src/api/chat.ts`, `src/types/chat.ts`

**기술 결정**: LangGraph (명시적 그래프, SSE 이벤트 분리, checkpointer), Gemini (비용)
**패키지**: langgraph, langchain-google-genai, langchain-core
**설정**: google_api_key, gemini_pro_model, gemini_lite_model
**파일 집계**: 신규 18 / 수정 5 / Migration 1

#### Phase C: 분석 시나리오 API — ⬜ 미시작 [개요 — 상세는 진입 시 dev-docs]

**목적**: 상관/지표/전략 분석을 챗봇 Tool로 제공
**상세 기획 시점**: Phase B 완료 후, dev-docs로 시나리오/응답 구조 확정

**예상 산출물**:
- 상관도 설명 API (`POST /v1/analysis/correlation/explain`)
- 지표 계산/해석 API (`POST /v1/analysis/indicators`)
- 전략 비교 API (`POST /v1/analysis/strategies/compare`)
- 차트 오버레이/정규화 요청 처리
- 분석 응답 스키마 + 차트 액션 매핑 규칙

**파일 집계 (추정)**: 신규 ~5 / 수정 ~2 / Migration 0

#### Phase D: 그래프 커스터마이징 통합 — ⬜ 미시작 [개요 — 상세는 진입 시 dev-docs]

**목적**: 대화 → 차트 반영, preset 저장, 페이지 재편
**상세 기획 시점**: Phase C 완료 후, dev-docs로 config_json 구조/UI 액션 매핑 확정

**예상 산출물**:
- `chart_presets` DB 테이블
- Backend: preferences/chart-actions API
- Frontend: chartStore (Zustand), ChartControls, IndicatorSignalPage
- chat-to-chart reducer (UI 액션 → 프론트 상태 변경)
- 페이지 구조 재편: 홈/가격/상관/지표시그널/전략

**파일 집계 (추정)**: 신규 ~12 / 수정 ~9 / Migration 1

#### Phase E: Memory + Retrieval — ⬜ 미시작 [개요 — 상세는 진입 시 dev-docs]

**사전 확인**: Railway PostgreSQL pgvector 지원 여부
**상세 기획 시점**: Phase D 완료 후, dev-docs로 메모리 데이터 타입/embedding 대상 확정

**예상 산출물**:
- `user_memories`, `retrieval_chunks`, `analysis_snapshots` DB 테이블
- Memory CRUD API
- SQL 우선 + pgvector 보조 검색 계층
- LangGraph retrieval 노드 + 임베딩 인덱싱
- 패키지: pgvector, langchain-community (pgvector retriever)

**기술 결정**: pgvector (Railway 지원 여부 Phase E 전 확인), Embedding 모델 Phase E 진입 시 결정
**파일 집계 (추정)**: 신규 ~13 / 수정 ~3 / Migration 1

#### Phase F: Onboarding + 운영 안정화 — ⬜ 미시작 [개요 — 상세는 진입 시 dev-docs]

**목적**: 사용자 온보딩 + 운영 방어
**상세 기획 시점**: Phase E 완료 후, dev-docs로 온보딩 메뉴/질문 항목 확정

**예상 산출물**:
- `onboarding_profiles` DB 테이블
- 온보딩 API/UI (관심 자산/전략/알림 수집)
- Gemini 3.1 Flash Lite (분류/온보딩 경량 모델)
- 프롬프트 인젝션/권한 우회/비용 한도 방어
- 품질 모니터링 대시보드

**파일 집계 (추정)**: 신규 ~10 / 수정 ~3 / Migration 1

## 5. 데이터 흐름

### MVP 데이터 흐름 (현재)
```
GitHub Actions cron (KST 18:00) → collector (FDR) → price_daily
                                   ↓
                         research_engine (preprocessing → factors → signals → backtest)
                                   ↓
                         factor_daily / signal_daily / backtest_* DB
                                   ↓
                         API (FastAPI, 12 endpoints)
                                   ↓
                         Frontend (React + Recharts, 6 pages)
```

### Post-MVP 데이터 흐름 (목표)
```
[기존 MVP 흐름] + 아래 추가:

사용자 → Auth (JWT) → Chat API (SSE) → LangGraph (StateGraph)
                                              ↓
                                   Tool 호출: 분석 서비스 (상관/지표/전략)
                                              ↓
                                   Retrieval: SQL 우선 + pgvector 보조
                                              ↓
                                   응답: text + citations + ui_actions
                                              ↓
                                   Frontend: Zustand → 차트 반영 + 메모리 저장
```

## 6. Risks & Mitigation (리스크 및 완화)

### MVP 리스크 (해소 완료)
| Risk | Status |
|------|--------|
| FDR 단일 소스 장애 | KS200 fallback 구현, 부분 성공 허용 |
| Railway PostgreSQL 연결 불안정 | TLS, 커넥션 풀링, 헬스체크 운영 중 |
| Windows 단일 호스트 장애 | GitHub Actions cron으로 해소 |
| GitHub Actions cron 지연 | 허용 범위 (장 마감 후) |

### Post-MVP 리스크
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LLM 잘못된 UI 액션 생성 | 차트 오류 | 중 | 제한된 액션 타입 allowlist + JSON schema 검증 |
| Gemini API 비용 초과 | 운영비 증가 | 중 | 토큰 사용량 컬럼 미리 설계, Flash Lite 경량 모델 병용 |
| pgvector Railway 미지원 | 벡터 검색 불가 | 저 | Phase E 전 확인, 대안: 별도 벡터 엔진 |
| Vector 검색이 수치 근거보다 앞설 경우 | 설명 품질 저하 | 중 | SQL 계산 우선, Vector는 보조 근거만 |
| 전략 비교 기간 민감도 | 오해 유발 | 저 | 6M/1Y/2Y 비교 기본 제공, 계산 기준 명시 |
| 사용자 메모리 ↔ 공용 분석 혼재 | 개인화 저하 | 저 | memory/retrieval source 분리, 출처 메타데이터 |
| 프롬프트 인젝션 | 보안 침해 | 중 | Phase F에서 방어 구현 |

## 7. Dependencies (의존성)

### 외부 (MVP — 운영 중)
- **Railway PostgreSQL**: DB 호스팅 ✅
- **FinanceDataReader**: 전 자산 데이터 소스 ✅
- **Discord Webhook**: 알림 채널 ✅
- **GitHub Actions**: CI/CD + cron ✅
- **Vercel**: 프론트엔드 호스팅 ✅

### 외부 (Post-MVP — 신규)
- **Google Gemini API**: LLM (Gemini 3.1 Pro + Flash Lite)
- **pgvector**: PostgreSQL 벡터 검색 확장 (Railway 지원 확인 필요)
- **langgraph + langchain-core + langchain-google-genai**: LLM 오케스트레이션

### 기술
- Python 3.12.3, Node.js 18+, PostgreSQL 15+ (Railway)
- venv: `backend/.venv/` (Windows)
- **신규**: python-jose, passlib (Auth), langgraph, Zustand (Frontend)
