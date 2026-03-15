# Project Overall Plan
> Last Updated: 2026-03-15
> Status: MVP 완료 (Phase 0~7), Phase A~D 완료, Phase D-rev 계획 수립 완료

## 1. Summary (개요)

**목적**: 7개 자산(KOSPI200, 삼성전자, SK하이닉스, SOXL, BTC, Gold, Silver)의 일봉 데이터 수집/저장/분석/시각화 MVP → **대화형 분석 워크스페이스**로 확장.

**범위**:
- **MVP (완료)**: Phase 0~7 — 수집 → 분석 → API → 대시보드 → 배포 → 자동 수집
- **Post-MVP (계획)**: Phase A~G — 인증 → 챗봇 → 상관도 → 지표 → 전략 → 메모리/벡터 → 온보딩

**MVP 결과물**:
- FDR 기반 일봉 수집 파이프라인 ✅
- PostgreSQL 데이터 저장소 (Railway) ✅
- 팩터/전략/백테스트 분석 엔진 ✅
- FastAPI 조회/백테스트/집계 API (12개 엔드포인트) ✅
- React + Recharts 대시보드 SPA (6개 페이지) ✅
- GitHub Actions cron 일일 자동 수집 ✅

**Post-MVP 목표 결과물**:
- JWT 인증 + 사용자 컨텍스트 ✅
- LangGraph + OpenAI GPT-5 기반 챗봇 (SSE 스트리밍) ✅
- 상관도 페이지 완성 (분석+하이브리드 응답+그래프 커스텀)
- 지표 페이지 완성 (성공률+예측력 비교+오버레이 차트)
- 전략 페이지 완성 (이벤트 스토리텔링+에쿼티 마커+기간 설정)
- 사용자 메모리 + pgvector 보조 검색
- 온보딩 에이전트

## 2. Current State (현재 상태)

- **MVP Phase 0~7**: 83/83 tasks 완료
- **Phase 1~3**: 골격 + 수집 + 분석 엔진
- **Phase 4**: FastAPI 12 endpoints, 405 tests
- **Phase 5**: React SPA 6페이지, UX 검증 완료
- **Phase 6**: CI/CD + Railway + Vercel 배포
- **Phase 7**: GitHub Actions cron 일일 자동 수집 (6/6 완료)
- **Phase A Auth**: 16/16 tasks 완료 (JWT 인증 + Frontend Auth)
- **Phase B Chatbot**: 19/19 tasks 완료 (LangGraph + OpenAI GPT-5, 심층모드)
- **Phase C 상관도**: 12/12 Steps 완료 (상관도 페이지 완성)
- **Phase C-rev2**: 완료 — 넛지 질문 품질 개선, LangSmith 트레이싱, 3-패널 SpreadChart (`ba30728`)
- **Phase D 지표**: 12/12 완료 — 지표 해석, 성공률, 비교, REST API, 프론트 3탭 (`d0392b6`~`7dc230f`)
- **Git**: `master` 브랜치, 647 passed, ruff clean
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
| **인증** | JWT 인증, 사용자별 데이터 격리 | ✅ Phase A |
| **챗봇** | LangGraph + OpenAI GPT-5 대화형 분석 + 심층모드 | ✅ Phase B |
| **상관도 페이지** | 그룹핑/유사자산, 스프레드, 하이브리드 응답, 관심종목 | ✅ Phase C |
| **상관도 피드백** | 종목명 표시, 히트맵 연동, 가격 오버레이, 채팅 UX | ✅ Phase C-rev |
| **지표 페이지** | 성공률, 예측력 비교, 오버레이 차트, REST 분석 API | ✅ Phase D |
| **지표 피드백** | 전략→지표 전환, 탭 통합, 레이아웃 개선, 정규화 버그 | ⬜ Phase D-rev |
| **전략 페이지** | 이벤트 스토리텔링, 에쿼티 마커, 기간 설정, 라우트 정리 | ⬜ Phase E |
| **메모리/검색** | 사용자 메모리 + pgvector 보조 검색 | ⬜ Phase F |
| **온보딩** | 관심 자산/전략/알림 수집, 가이드 | ⬜ Phase G |

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

### Post-MVP Phases (Phase A~G) — A/B 완료, C~G 계획

> 참조: `docs/post-mvp-implementation-sketch.md` (제품 요구사항)
> 통합 계획: `docs/post-mvp-phaseCD-detail.md` (Phase C~E 상세)

**구현 순서**: `A (Auth) → B (Chat) → C (상관도) → D (지표) → E (전략) → F (Memory+Vector) → G (Onboarding)`
**설계 원칙**: 기존 Phase C(분석 시나리오)+D(그래프 커스텀)를 **페이지별로 분리** — 각 페이지를 백엔드+프론트+챗봇까지 완결한 뒤 다음 페이지로 이동.

#### Phase A: Auth + 사용자 컨텍스트 — ✅ 완료 (16/16) [상세 확정]
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
**기술 결정**: python-jose + bcrypt 직접 사용 (passlib 제거 — bcrypt 5.x 호환)
**파일 집계**: 신규 14 / 수정 6 / Migration 1
**완료**: 16/16 tasks — `49f9928`~`fcdeed3`

#### Phase B: Chatbot 기본 루프 — ✅ 완료 (19/19) [상세 확정]

**목적**: LangGraph + OpenAI GPT-5 기반 대화형 분석 루프

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

**기술 결정**: LangGraph (명시적 그래프, SSE 이벤트 분리, checkpointer), OpenAI GPT-5 (Gemini 쿼타 초과로 전환)
**패키지**: langgraph 1.1.1, langchain-openai 1.1.11, langchain-core 1.2.18
**설정**: openai_api_key, llm_pro_model (gpt-5), llm_lite_model (gpt-5-mini)
**심층모드**: 기본 GPT-5 Mini, 토글 시 GPT-5 (정밀 분석)
**파일 집계**: 신규 18 / 수정 8 / Migration 1
**완료**: 19/19 tasks — `936bc9a`~`2202455`

#### Phase C: 상관도 페이지 완성 — ✅ 완료 (12/12 Steps)
> dev-docs: `dev/active/phaseC-correlation/`

**목적**: 상관도 분석 서비스 + 스프레드 + 하이브리드 응답 기반 + 프론트 확장 + 관심 종목
**핵심 신규 기능**: 스프레드 차트 (z-score 밴드), 하이브리드 응답 (정규표현식 분류기+템플릿+LLM fallback), 넛지 질문

**Backend 산출물**:
- `api/services/analysis/correlation_analysis.py` — 그룹핑(Union-Find), 유사자산, top pairs
- `api/services/analysis/spread_service.py` — 정규화 스프레드 + z-score 수렴/발산 감지
- `api/services/analysis/interpretation_rules.py` — 상관도/스프레드 해석 상수
- `api/services/llm/tools.py` 수정 — `analyze_correlation`, `get_spread` Tool 추가
- `api/services/llm/hybrid/` 디렉토리 — `context.py`, `classifier.py`, `templates.py`, `actions.py`
- `api/services/llm/graph.py` 수정 — 하이브리드 분류기 통합
- `api/services/chat/chat_service.py` 수정 — page_context + SSE ui_action 확장

**Frontend 산출물**:
- `src/store/chartActionStore.ts` — Zustand (UI 액션 큐)
- `src/store/watchlistStore.ts` — Zustand + localStorage (관심 종목)
- `src/components/charts/ScatterPlotChart.tsx`, `SpreadChart.tsx`
- `src/components/correlation/CorrelationGroupCard.tsx`
- `src/components/chat/NudgeQuestions.tsx`
- `src/components/common/WatchlistToggle.tsx`
- `src/hooks/useSSE.ts`, `src/types/chat.ts`, `src/api/chat.ts` 수정
- `src/pages/CorrelationPage.tsx`, `src/components/chat/ChatPanel.tsx` 수정

**설계 결정**:
- 하이브리드 분류기 = 정규표현식+키워드 (LLM intent classification 안 씀 → 레이턴시 최소화)
- 분류 실패 시 LangGraph LLM fallback
- SSE `ui_action` 이벤트로 프론트 차트 제어

**파일 집계**: 신규 ~13 / 수정 ~9 / Migration 0
**완료**: 12/12 Steps — `3cf57f7`~`f03188a`

#### Phase C-rev: 상관도 페이지 피드백 반영 — ✅ 완료 (7/7 Tasks)
> dev-docs: `dev/active/phaseC-revision/`
> Source: `docs/post-mvp-feedback.md` (프로덕션 브라우저 리뷰)

**목적**: Phase C 프로덕션 리뷰에서 발견된 UX 이슈 7건 수정
**핵심 변경**: 종목명 표시, 히트맵 인터랙션 통합, 가격 오버레이 차트, 채팅 대기 UX, 넛지 템플릿 보장

**수정 항목**:
1. 종목 코드 → 종목명 표시 + 그래프별 설명 텍스트
2. 상관계수 분포 차트 삭제
3. 히트맵 셀 클릭 → Scatter+Spread 연동 (3종목 그룹 페어 선택 포함)
4. 스프레드: 정규화 가격 오버레이(상단) + Z-score 밴드(하단) 2-패널
5. 채팅: 스트림 시작 전 타이핑 인디케이터 + status SSE 이벤트
6. 넛지 질문: is_nudge 플래그 → 템플릿 응답 보장 (LLM 호출 제거)
7. LangSmith 트레이싱 (환경변수 설정 완료)

**파일 집계**: 수정 Backend ~6 / Frontend ~10 / 신규 0

#### Phase D: 지표 페이지 완성 — ✅ 완료 (12/12 Tasks)
> dev-docs: `dev/active/phaseD-indicators/`

**목적**: 지표 현재 상태 해석 + 매수/매도 성공률 + 예측력 비교 + REST API + 프론트 통합 페이지
**핵심 신규 기능**: 지표 매수/매도 성공률 (forward 5일), 지표 간 예측력 비교, 분석 REST 엔드포인트

**Backend 산출물**:
- `api/services/analysis/indicator_analysis.py` — `INDICATOR_RULES` + `interpret_indicator_state()`
- `api/services/analysis/signal_accuracy_service.py` — 성공률 계산 (signal=1 → 5일 후 close 비교)
- `api/services/analysis/indicator_comparison.py` — 3개 전략 예측력 비교
- `api/schemas/analysis.py` — 분석 요청/응답 Pydantic 스키마
- `api/routers/analysis_router.py` — `GET /v1/analysis/signal-accuracy`, `GET /v1/analysis/indicator-comparison`
- `api/services/llm/tools.py` 수정 — `analyze_indicators` Tool 추가
- `api/services/llm/hybrid/templates.py`, `classifier.py` 수정 — 지표 카테고리 확장

**Frontend 산출물**:
- `src/pages/IndicatorSignalPage.tsx` — 탭: 지표 현황 / 시그널 타임라인 / 성공률
- `src/components/charts/IndicatorOverlayChart.tsx` — ComposedChart (가격+지표 오버레이)
- `src/components/analysis/AccuracyTable.tsx` — 색상코딩 성공률 테이블
- `src/components/charts/AccuracyBarChart.tsx` — 성공률 막대 차트
- `src/components/common/IndicatorSettingsPanel.tsx` — 표시/숨기기/정규화 토글
- `src/api/analysis.ts` — `fetchSignalAccuracy()`, `fetchIndicatorComparison()`
- `src/App.tsx` 수정 — `/indicators` 라우트 + redirect
- `src/components/layout/Sidebar.tsx` 수정 — 네비 통합

**설계 결정**:
- REST 엔드포인트 추가 (성공률/비교는 UI 페이지에서 직접 표시 필요)
- 기존 FactorPage/SignalPage 파일 유지, 라우트만 `/indicators`로 redirect
- 넛지 질문: "현재 RSI 상태가 궁금하신가요?", "지표 성공률을 확인해볼까요?"

**파일 집계**: 신규 ~10 / 수정 ~7 / Migration 0
**완료**: 12/12 tasks — `d0392b6`~`7dc230f`

#### Phase D-rev: 지표 페이지 피드백 반영 — ⬜ 계획 수립 완료 (10 Tasks) [상세 확정]
> dev-docs: `dev/active/phaseD-revision/`
> Source: `docs/post-mvp-feedback.md` Phase D 섹션

**목적**: 전략(momentum/trend/mean_reversion) → 개별 지표(RSI/MACD/ATR+vol) 단위 전환, 탭 통합, 레이아웃 개선
**핵심 변경**: 지표별 on-the-fly 시그널 생성, 3탭→2탭 통합, 3/4+1/4 레이아웃, 정규화 버그 수정

**수정 항목**:
1. 지표별 시그널 생성 서비스 (factor_daily → on-the-fly 시그널)
2. 성공률/비교 서비스 — strategy_id → indicator_id 전환
3. API 엔드포인트 수정 + indicator-signals 신규
4. 3탭→2탭(시그널/성공률) + 전략 배제
5. 시그널 탭: 차트 3/4 + 설명 1/4, Y축 수직 점선
6. 성공률 탭: 차트 3/4 + 거래 성공/실패 테이블 1/4
7. 정규화 0 스파이크 버그 수정
8. ATR(+vol) 위험 구간 특수 처리

**파일 집계**: 신규 ~2 / 수정 ~11 / Migration 0

#### Phase E: 전략 페이지 완성 — ⬜ 미시작 (9 Steps) [상세 확정]
> dev-docs: `dev/active/phaseE-strategy/`

**목적**: 전략 비교 분석 + 이벤트 스토리텔링 + 에쿼티 이벤트 마커 + 기간 설정 + 라우트 최종 정리
**핵심 신규 기능**: 이벤트 스토리텔링 (하드코딩 템플릿+f-string), on-the-fly 경량 백테스트

**Backend 산출물**:
- `api/services/analysis/strategy_analysis.py` — on-the-fly 전략 비교 (DB 저장 없음)
- `api/services/analysis/storytelling_service.py` — `generate_trade_narratives()`, `generate_strategy_story()`
- `api/routers/analysis_router.py` 수정 — `POST /v1/analysis/strategy-comparison`
- `api/schemas/analysis.py` 수정 — 전략 비교 요청/응답 스키마
- `api/services/llm/tools.py` 수정 — `compare_strategies` Tool 추가
- `api/services/llm/hybrid/templates.py`, `classifier.py` 수정 — 전략 카테고리 확장

**Frontend 산출물**:
- `src/components/strategy/StrategyDescriptionCard.tsx` — 3개 전략별 설명 (접힘/펼침)
- `src/components/charts/EquityCurveWithEvents.tsx` — ReferenceDot 매매 포인트
- `src/components/strategy/TradeNarrativePanel.tsx` — 클릭 시 내러티브 카드
- `src/api/analysis.ts` 수정 — `fetchStrategyComparison()` 추가
- `src/pages/StrategyPage.tsx` 수정 — 설명 카드, 이벤트 마커, 6M/1Y/2Y 기간
- `src/components/layout/Sidebar.tsx` 수정 — 5개 항목 최종 정리
- `src/App.tsx` 수정 — `/factors`, `/signals` → `/indicators` redirect 확인

**설계 결정**:
- 스토리텔링 = 하드코딩 템플릿+f-string (추상 점수 금지, 실제 금액/수익률만)
- on-the-fly 백테스트 (DB 저장 안 함) — DB에 없는 기간 조합도 즉시 비교
- 전략 설명 하드코딩 (모멘텀="달리는 말에 타는 전략…")
- 기존 FactorPage.tsx, SignalPage.tsx 파일 유지 (삭제 안 함)

**파일 집계**: 신규 ~7 / 수정 ~7 / Migration 0

#### Phase F: Memory + Retrieval — ⬜ 미시작 [개요 — 상세는 진입 시 dev-docs]

**사전 확인**: Railway PostgreSQL pgvector 지원 여부
**상세 기획 시점**: Phase E 완료 후, dev-docs로 메모리 데이터 타입/embedding 대상 확정

**예상 산출물**:
- `user_memories`, `retrieval_chunks`, `analysis_snapshots` DB 테이블
- Memory CRUD API
- SQL 우선 + pgvector 보조 검색 계층
- LangGraph retrieval 노드 + 임베딩 인덱싱
- 패키지: pgvector, langchain-community (pgvector retriever)

**기술 결정**: pgvector (Railway 지원 여부 Phase F 전 확인), Embedding 모델 Phase F 진입 시 결정
**파일 집계 (추정)**: 신규 ~13 / 수정 ~3 / Migration 1

#### Phase G: Onboarding + 운영 안정화 — ⬜ 미시작 [개요 — 상세는 진입 시 dev-docs]

**목적**: 사용자 온보딩 + 운영 방어
**상세 기획 시점**: Phase F 완료 후, dev-docs로 온보딩 메뉴/질문 항목 확정

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
| pgvector Railway 미지원 | 벡터 검색 불가 | 저 | Phase F 전 확인, 대안: 별도 벡터 엔진 |
| Vector 검색이 수치 근거보다 앞설 경우 | 설명 품질 저하 | 중 | SQL 계산 우선, Vector는 보조 근거만 |
| 전략 비교 기간 민감도 | 오해 유발 | 저 | 6M/1Y/2Y 비교 기본 제공, 계산 기준 명시 |
| 사용자 메모리 ↔ 공용 분석 혼재 | 개인화 저하 | 저 | memory/retrieval source 분리, 출처 메타데이터 |
| 프롬프트 인젝션 | 보안 침해 | 중 | Phase G에서 방어 구현 |

## 7. Dependencies (의존성)

### 외부 (MVP — 운영 중)
- **Railway PostgreSQL**: DB 호스팅 ✅
- **FinanceDataReader**: 전 자산 데이터 소스 ✅
- **Discord Webhook**: 알림 채널 ✅
- **GitHub Actions**: CI/CD + cron ✅
- **Vercel**: 프론트엔드 호스팅 ✅

### 외부 (Post-MVP — 신규)
- **OpenAI API**: LLM (GPT-5 + GPT-5 Mini)
- **pgvector**: PostgreSQL 벡터 검색 확장 (Railway 지원 확인 필요)
- **langgraph + langchain-core + langchain-openai**: LLM 오케스트레이션

### 기술
- Python 3.12.3, Node.js 18+, PostgreSQL 15+ (Railway)
- venv: `backend/.venv/` (Windows)
- **신규**: python-jose, bcrypt (Auth), langgraph, langchain-core, langchain-openai, Zustand (Frontend)
