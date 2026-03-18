# Project Overall Tasks
> Last Updated: 2026-03-17
> Status: MVP 완료 (83/83), Phase A~E 완료, Phase F 계획 중, Phase G~H 미시작

## Phase 0: 사전 준비 ✅ 완료
- [x] 마스터플랜 작성 (docs/masterplan-v0.md)
- [x] 데이터 접근성 검증 (Conditional Go)
- [x] CLAUDE.md + Skills + Hooks 설정
- [x] Git 초기화 + remote 설정 + push
- [x] Kiwoom 폐기, FDR 단일 소스 결정

## Phase 1: 프로젝트 골격 + DB ✅ 완료 (9/9)
- [x] 1.1 `pyproject.toml` + 의존성 설치 `[S]`
- [x] 1.2 `.env.example` + `DATABASE_URL` 설정 `[S]`
- [x] 1.3 `db/models.py` — SQLAlchemy 모델 8개 테이블 `[M]`
- [x] 1.4 Alembic 초기화 + 초기 마이그레이션 `[M]`
- [x] 1.5 `asset_master` 시드 스크립트 `[S]`
- [x] 1.6 `config/settings.py` — Pydantic BaseSettings `[S]`
- [x] 1.7 `config/logging.py` — JSON 로깅 설정 `[S]`
- [x] 1.8 `db/session.py` — SessionLocal 엔진 `[S]`
- [x] 1.9 기본 단위 테스트 `[M]`

## Phase 2: 수집기 (Collector) ✅ 완료 (10/10)
- [x] 2.1 `collector/fdr_client.py` — FDR 래퍼 + 심볼 매핑 `[M]`
- [x] 2.2 `collector/validators.py` — OHLCV 정합성 검증 `[M]`
- [x] 2.3 `collector/ingest.py` — 수집 오케스트레이션 `[L]`
- [x] 2.4 지수 백오프 재시도 로직 `[M]`
- [x] 2.5 idempotent UPSERT 구현 `[M]`
- [x] 2.6 부분 실패 허용 + `job_run` 기록 `[M]`
- [x] 2.7 정합성 검증 강화 `[S]`
- [x] 2.8 `collector/alerting.py` — Discord 알림 `[S]`
- [x] 2.9 `scripts/collect.py` — 수집 배치 CLI `[M]`
- [x] 2.10 3년 백필 실행 + 검증 (5,559 rows) `[L]`

## Phase 3: 분석 엔진 (Research Engine) ✅ 완료 (12/12)
- [x] 3.1 전처리 파이프라인 `[M]` — `d476c52`
- [x] 3.2 수익률 + 추세 팩터 `[M]` — `b1ce303`
- [x] 3.3 모멘텀 + 변동성 + 거래량 팩터 `[M]` — `b1ce303`
- [x] 3.4 팩터 DB 저장 `[M]` — `1e35fd9`
- [x] 3.5 전략 프레임워크 `[M]` — `6956015`
- [x] 3.6 3종 전략 구현 `[M]` — `6956015`
- [x] 3.7 시그널 생성 + DB 저장 `[S]` — `6956015`
- [x] 3.8 백테스트 엔진 `[L]` — `da01cef`
- [x] 3.9 성과 평가 지표 `[M]` — `c433392`
- [x] 3.10 백테스트 결과 DB 저장 `[S]` — `4f9cdc9`
- [x] 3.11 배치 스크립트 + 통합 테스트 `[M]` — `fc8fc4f`
- [x] 3.12 dev-docs 갱신 `[S]`

## Phase 4: API ✅ 완료 (15/15)
> dev-docs: `dev/active/phase4-api/`

### 4A. 기반 구조 ✅
- [x] 4.1 FastAPI 앱 골격 (main.py, CORS, error handler, DI) `[M]`
- [x] 4.2 Pydantic 스키마 정의 `[M]` — `77e4b1d`
- [x] 4.3 Repository 계층 (DB 접근 추상화) `[M]` — `b990914`

### 4B. 조회 API ✅
- [x] 4.4 `GET /v1/health` `[S]`
- [x] 4.5 `GET /v1/assets` `[S]`
- [x] 4.6 `GET /v1/prices/daily` `[M]`
- [x] 4.7 `GET /v1/factors` `[M]`
- [x] 4.8 `GET /v1/signals` `[M]`

### 4C. 백테스트 API ✅
- [x] 4.9 `GET /v1/backtests` `[S]` — `fac9e08`
- [x] 4.10 `GET /v1/backtests/{run_id}` + `/equity` + `/trades` `[M]` — `fac9e08`
- [x] 4.11 `POST /v1/backtests/run` `[L]` — `bb05a35`

### 4D. 집계 API + 테스트 ✅
- [x] 4.12 `GET /v1/dashboard/summary` `[M]` — `3171061`
- [x] 4.13 `GET /v1/correlation` `[M]` — `7ddb5f0`
- [x] 4.14 API 단위 + 통합 테스트 `[M]` — `1d10c2e`

### 4E. E2E 검증 ✅
- [x] 4.15 E2E 파이프라인 실행 `[M]`

## Phase 5: 프론트엔드 (Frontend) ✅ 완료 (13/13)
> dev-docs: `dev/active/phase5-frontend/`

### 5A. 기반 구조 ✅
- [x] 5.1 Vite + React + TypeScript 초기화 `[M]` — `f227b2b`
- [x] 5.2 API 클라이언트 + 타입 정의 `[M]` — `f227b2b`
- [x] 5.3 레이아웃 (사이드바 + 메인 콘텐츠) `[M]` — `f227b2b`

### 5B. 핵심 차트 ✅
- [x] 5.4 가격 차트 `[L]` — `91effb9`
- [x] 5.5 수익률 비교 차트 `[M]` — `91effb9`

### 5C. 분석 시각화 ✅
- [x] 5.6 상관 히트맵 `[M]` — `048d34d`
- [x] 5.7 팩터 현황 `[M]` — `3b8ceed`
- [x] 5.8 시그널 타임라인 `[M]` — `d0bf7a4`

### 5D. 전략 성과 + 홈 ✅
- [x] 5.9 전략 성과 비교 `[L]` — `aafa80d`
- [x] 5.10 대시보드 홈 `[M]` — `3b583a9`

### 5E. UX 디버깅 ✅
- [x] 5.11 UX 버그: 전략 ID + X축 정렬 `[M]` — `398f7da`
- [x] 5.12 UX 버그: Gold/Silver 에러 + 거래량 `[M]` — `398f7da`
- [x] 5.13 UX 버그: 팩터/전략 데이터 `[S]` — `398f7da`, `d227ee9`

## Phase 6: 배포 & 운영 ✅ 완료 (9/9)
> dev-docs: `dev/active/phase6-deploy/`

### 6A. 배치 통합
- [x] 6.1 리서치 파이프라인 배치 스케줄링 `[S]` — `c80fd08`
- [x] 6.4 로그 로테이션 `[S]` — `c80fd08`

### 6B. 테스트 검증
- [x] 6.2 테스트 전체 실행 & 검증 `[M]` — `66cbef1`

### 6C. 운영 도구
- [x] 6.3 Pre-deployment 체크 스크립트 `[M]` — `93407b4`

### 6D. CI/CD
- [x] 6.7 GitHub Actions CI 파이프라인 `[M]` — `4b263b9`

### 6E. 프로덕션 배포
- [x] 6.8 백엔드 Railway 배포 `[M]` — `e80d50b`
- [x] 6.9 프론트엔드 Vercel 배포 `[M]` — `f745079`

### 6F. 문서화
- [x] 6.5 운영 문서 (Runbook) `[M]` — `65e6703`
- [x] 6.6 dev-docs 갱신 `[S]`

## Phase 7: 스케줄 자동 수집 ✅ 완료 (6/6)
> dev-docs: `dev/active/phase7-scheduler/`

### 7A. 사전 준비
- [x] 7.1 Railway Public Networking 확인 `[S]`
- [x] 7.2 GitHub Secrets 등록 `[S]`

### 7B. Workflow 구현
- [x] 7.3 `daily-collect.yml` 작성 `[M]` — `b798b65`

### 7C. 검증 + 문서
- [x] 7.4 workflow_dispatch E2E 검증 `[M]`
- [x] 7.5 Runbook 업데이트 `[S]`
- [x] 7.6 dev-docs 갱신 `[S]`

---

## Post-MVP Phases (Phase A~F) — 계획

> 구현 순서: A → B → C → D → E → F → G → H
> Phase A~E: 완료. Phase F: 상세 확정 (10 tasks). Phase G~H: 진입 시 `/dev-docs`로 상세 기획.

## Phase A: Auth + 사용자 컨텍스트 — ✅ 완료 (16/16)
> dev-docs: `dev/active/phaseA-auth/`

### Stage A: Backend 기반
- [x] A.1 DB 모델: User, UserSession + Alembic migration `[M]` → `49f9928`
- [x] A.2 Settings: jwt_secret_key, jwt_algorithm, access/refresh TTL `[S]` → `6bbc6bb`
- [x] A.3 Pydantic 스키마: auth.py `[S]` → `2c3e9a4`
- [x] A.4 Repository: user_repo.py, session_repo.py `[M]` → `3d85590`

### Stage B: Backend Auth 로직
- [x] A.5 Service: auth_service.py `[L]` → `0ea34b7`
- [x] A.6+A.7 Router + Dependencies `[M]` → `66fc0e1`

### Stage C: Backend 통합 + 테스트
- [x] A.8 main.py 라우터 등록 + pyproject.toml 의존성 `[S]` → `985c093`
- [x] A.9+A.10 Auth 테스트 16개 + Regression `[M]` → `4e1419f`

### Stage D: Frontend Auth
- [x] A.11~A.15 Frontend Auth 전체 `[M]` → `fcdeed3`

### Stage E: E2E 검증 + 문서
- [x] A.16 E2E 검증 `[M]` — 프로덕션 확인 완료
- [x] A.17 dev-docs 갱신 `[S]` → `566bb96`

## Phase B: Chatbot 기본 루프 — ✅ 완료 (19/19)
> dev-docs: `dev/active/phaseB-chatbot/`

### Stage A: Backend LLM 기반
- [x] B.1 Settings: openai_api_key, llm_pro/lite_model `[S]` — `936bc9a`, `807c33f`
- [x] B.2 LangGraph graph.py: StateGraph + deep_mode `[L]` — `936bc9a`, `807c33f`, `2202455`
- [x] B.3 LangChain tools.py: 5개 Tool `[M]` — `936bc9a`
- [x] B.4 prompts.py: 시스템 프롬프트 `[S]` — `936bc9a`

### Stage B: Backend Chat 데이터
- [x] B.5 DB 모델: ChatSession, ChatMessage + migration `[M]` — `e73096a`
- [x] B.6 Pydantic 스키마: chat.py (+ deep_mode) `[S]` — `e73096a`, `2202455`
- [x] B.7 Repository: chat_repo.py `[M]` — `e73096a`

### Stage C: Backend Chat API
- [x] B.8 Service: chat_service.py (SSE + ToolMessage 수정) `[L]` — `fa112e6`, `689dedf`, `2202455`
- [x] B.9 Router: chat.py (4 endpoints) `[M]` — `fa112e6`
- [x] B.10 main.py 라우터 등록 + langchain-openai `[S]` — `fa112e6`, `807c33f`

### Stage D: Backend 테스트
- [x] B.11 단위 테스트: chat service + router (14건) `[M]` — `3d8dcd7`
- [x] B.12 Regression: 440 passed + ruff `[S]` — `3d8dcd7`

### Stage E: Frontend Chat
- [x] B.13 Frontend: types/chat.ts + api/chat.ts `[S]` — `5db4127`, `2202455`
- [x] B.14 Frontend: hooks/useSSE.ts `[M]` — `5db4127`
- [x] B.15 Frontend: store/chatStore.ts (+ deepMode) `[M]` — `5db4127`, `2202455`
- [x] B.16 Frontend: ChatPanel + MessageBubble + ChatInput (+ 심층모드) `[L]` — `5db4127`, `2202455`
- [x] B.17 Frontend: Layout에 ChatPanel 통합 `[S]` — `5db4127`, `2f21d0d`

### Stage F: E2E 검증 + 문서
- [x] B.18 E2E 검증 (Gemini→OpenAI 전환 + 프로덕션) `[M]` — `807c33f`, `689dedf`, `2f21d0d`
- [x] B.19 dev-docs 갱신 + 심층모드 `[S]` — `2202455`

## Phase C: 상관도 페이지 완성 — ✅ 완료 (12/12)
> dev-docs: `dev/active/phaseC-correlation/`
> **파일 집계**: 신규 ~13 / 수정 ~9 / Migration 0

### Stage A: Backend 분석 서비스
- [x] C.1 상관도 분석 서비스 — 그룹핑/유사자산 `[M]` → `3cf57f7`
- [x] C.2 스프레드 분석 서비스 `[M]` → `21e0b52`
- [x] C.3 해석 규칙 상수 정의 `[S]` → `21e0b52`

### Stage B: LangGraph Tool 확장
- [x] C.4 LangGraph Tool — `analyze_correlation` `[M]` → `e1d9e40`
- [x] C.5 LangGraph Tool — `get_spread` `[M]` → `e1d9e40`

### Stage C: 하이브리드 응답 기반
- [x] C.6 하이브리드 응답 기반 구축 (`hybrid/` 디렉토리) `[L]` → `2caf0d4`
- [x] C.7 하이브리드를 LangGraph에 통합 `[L]` → `4e2c15c`

### Stage D: Frontend 확장
- [x] C.8 SSE 확장 + chartActionStore `[M]` → `09fe91e`
- [x] C.9 상관도 페이지 확장 (그룹핑+Scatter) `[M]` → `edf759e`
- [x] C.10 SpreadChart + 넛지 질문 UI `[M]` → `17c4742`
- [x] C.11 관심 종목 설정 `[S]` → `17c16a7`

### Stage E: 통합 검증
- [x] C.12 Phase C 통합 검증 `[M]` → `f03188a`

## Phase C-rev: 상관도 피드백 반영 — ✅ 완료 (7/7)
> dev-docs: `dev/active/phaseC-revision/`
> **파일 집계**: 수정 Backend 8 / Frontend 10

### Stage A: 데이터 기반
- [x] CR.1 종목명 매핑 + 그래프 설명 `[M]` → `c89db7c`

### Stage B: 히트맵 인터랙션 통합
- [x] CR.2 상관계수 분포 삭제 `[S]` → `2c3f541`
- [x] CR.3 히트맵 셀 클릭 → Scatter+Spread 연동 + 그룹 페어 선택 `[L]` → `2c3f541`

### Stage C: 스프레드 차트 개선
- [x] CR.4 정규화 가격 오버레이 + Z-score 하단 2-패널 `[L]` → `a179168`

### Stage D: 채팅 UX 개선
- [x] CR.5 채팅 대기 UX (타이핑 인디케이터 + status 이벤트) `[M]` → `ac30443`
- [x] CR.6 넛지 질문 템플릿 응답 보장 (is_nudge 플래그) `[M]` → `ac30443`

### Stage E: 통합 검증
- [x] CR.7 Phase C-rev 통합 검증 + 프로덕션 배포 `[M]`

## Phase D: 지표 페이지 완성 — ✅ 완료 (12/12)
> dev-docs: `dev/active/phaseD-indicators/`
> **파일 집계**: 신규 ~10 / 수정 ~7 / Migration 0

### Stage A: Backend 분석 서비스
- [x] D.1 지표 분석 서비스 — 현재 상태 해석 `[M]` — `d0392b6`
- [x] D.2 지표 성공률 서비스 ⭐핵심 `[L]` — `d7c829b`
- [x] D.3 지표 간 예측력 비교 `[M]` — `2a971c5`

### Stage B: REST API + LangGraph
- [x] D.4 분석 REST 엔드포인트 `[M]` — `2a971c5`
- [x] D.5 LangGraph Tool — `analyze_indicators` `[M]` — `8ff4311`
- [x] D.6 하이브리드 응답 — 지표 카테고리 확장 `[S]` — `8ff4311`

### Stage C: Frontend 통합 페이지
- [x] D.7 IndicatorSignalPage 통합 `[L]` — `7dc230f`
- [x] D.8 지표 오버레이 차트 `[M]` — `7dc230f`
- [x] D.9 성공률 테이블/차트 `[M]` — `7dc230f`

### Stage D: Frontend 고도화
- [x] D.10 멀티 지표 설정 + 정규화 `[M]` — `7dc230f`
- [x] D.11 chartActionStore 연결 `[S]` — `7dc230f`

### Stage E: 통합 검증
- [x] D.12 Phase D 통합 검증 `[M]` — 647 tests, 프로덕션 배포 완료

## Phase D-rev: 지표 피드백 반영 — ✅ 12/13 완료 (DR.13 백필 잔여)
> dev-docs: `dev/active/phaseD-revision/`
> **파일 집계**: 신규 ~2 / 수정 ~11 / Migration 0

### Stage A: Backend — 지표별 시그널 생성
- [x] DR.1 지표별 시그널 생성 서비스 (indicator_signal_service.py 신규) `[L]` — `9073f05`
- [x] DR.2 지표별 성공률 계산 수정 `[M]` — `9073f05`

### Stage B: Backend — API + 비교 수정
- [x] DR.3 지표 비교 서비스 수정 (RSI vs MACD) `[M]` — `9073f05`
- [x] DR.4 API 엔드포인트 수정 + 신규 `[M]` — `9073f05`

### Stage C: Frontend — 탭 통합 + 레이아웃
- [x] DR.5 3탭→2탭 전환 + 전략 배제 `[L]` — `9073f05`
- [x] DR.6 시그널 탭 레이아웃 (차트 3/4 + 설명 1/4, 수직 점선) `[M]` — `9073f05`
- [x] DR.7 성공률 탭 레이아웃 (차트 3/4 + 거래 테이블 1/4) `[M]` — `9073f05`

### Stage D: Frontend — 버그 수정 + 특수 처리
- [x] DR.8 정규화 버그 수정 `[S]` — `9073f05`
- [x] DR.9 ATR(+vol) 특수 처리 `[S]` — `9073f05`

### Stage E: 추가 피드백 수정
- [x] DR.11 오버레이 지표 표시 + MACD 시그널라인 `[M]` — `92f964d`
- [x] DR.11b repo 쿼리 정렬 DESC→ASC 수정 `[S]` — `4301224`
- [x] DR.12 팩터 계산 lookback 확장 (LOOKBACK_DAYS=150) `[M]` — `d942cfc`
- [ ] DR.13 프로덕션 백필 + 통합 검증 `[M]`

## Phase D-improve: 지표 추가 개선 — ✅ 완료 (7/7)
- [x] DI.1~DI.7 지표 설명, T+3 frequency, RSI 해제, ATR 스케일, 기간 동기화 — `a4e4c16`
- [x] E2E 버그 수정 3건 (시그널 시각구분, MACD backfill, 성공률 탭 단순화) — `19daaa9`
- [x] 시그널 시각구분 강화 + 바차트/테이블 색상 고정 — `b359598`

## Phase E: 전략 페이지 완성 — ✅ 완료 (10/10)
> dev-docs: `dev/active/phaseE-strategy/`
> **파일 집계**: 신규 ~8 / 수정 ~8 / Migration 0
> **전략 재정의**: 모멘텀(MACD), 역발상(RSI), 위험회피(ATR+vol) — indicator_signal_service 활용

### Stage A: Backend 전략 백테스트 서비스
- [x] E.1 전략 백테스트 서비스 (indicator 시그널 → on-the-fly 백테스트) `[L]` — `7bd04ca`
- [x] E.2 연간 성과 분석 서비스 (1년 단위 슬라이싱 + 적합도) `[M]` — `baebc45`
- [x] E.3 이벤트 스토리텔링 서비스 (Best/Worst 식별 + 내러티브) `[L]` — `8bf845c`

### Stage B: REST + LangGraph
- [x] E.4 전략 백테스트 REST 엔드포인트 `[M]` — `3686246`
- [x] E.5 LangGraph Tool + 하이브리드 전략 확장 `[M]` — `3b9bf40`

### Stage C: Frontend
- [x] E.6 전략 사전 설명 카드 (모멘텀/역발상/위험회피) `[S]` — `cc69eb3`
- [x] E.7 에쿼티 커브 이벤트 마커 + Best/Worst annotation + 내러티브 ⭐핵심 `[XL]` — `cc69eb3`
- [x] E.8 연간 성과 차트 + 기간 설정 + 1억원 시드 `[L]` — `cc69eb3`
- [x] E.9 라우트 최종 정리 `[S]` — `cc69eb3`

### Stage D: 통합 검증
- [x] E.10 Phase E 통합 검증 `[M]` — `be8ecf1`

## Phase F: Full Agentic Flow — 📋 계획 중 (0/10)
> dev-docs: `dev/active/phaseF-agentic/`
> **파일 집계**: 신규 ~6 / 수정 ~6 / Migration 0

### Stage A: 기반 정의
- [ ] F.1 Pydantic 스키마 정의 (ClassificationResult, CuratedReport, UIActionModel) `[S]`
- [ ] F.2 Knowledge Expert Prompts (Classifier + 4개 페이지 전문가) `[S]`

### Stage B: 핵심 모듈 구현
- [ ] F.3 LLM Classifier (Structured Output, gpt-5-mini) `[M]` — depends: F.1, F.2
- [ ] F.4 DataFetcher (tool 프로그래밍적 호출, 동적 매핑) `[M]` — depends: F.1
- [ ] F.5 LLM Reporter (Structured Output, knowledge prompt) `[M]` — depends: F.1, F.2

### Stage C: 백엔드 통합
- [ ] F.6 chat_service.py 통합 (agentic flow 전환) `[L]` — depends: F.3, F.4, F.5

### Stage D: 프론트엔드 확장
- [ ] F.7 follow_up SSE + 프론트엔드 UI `[S]` — depends: F.6
- [ ] F.8 프론트엔드 navigate 핸들러 (즉시 이동) `[S]` — depends: F.6

### Stage E: 정리 + 검증
- [ ] F.9 레거시 코드 정리 (regex classifier, templates) `[S]` — depends: F.6~F.8
- [ ] F.10 통합 검증 (pytest + tsc + vite + E2E) `[M]` — depends: F.1~F.9

## Phase G: Memory + Retrieval — ⬜ 미시작
> 상세 태스크: Phase G dev-docs 생성 시 확정
> **파일 집계 (추정)**: 신규 ~13 / 수정 ~3 / Migration 1

## Phase H: Onboarding + 운영 안정화 — ⬜ 미시작
> 상세 태스크: Phase H dev-docs 생성 시 확정
> **파일 집계 (추정)**: 신규 ~10 / 수정 ~3 / Migration 1

---

## Summary

### MVP (완료)
- **Phase 0**: 5 tasks ✅
- **Phase 1**: 9 tasks ✅
- **Phase 2**: 10 tasks ✅
- **Phase 3**: 12 tasks ✅
- **Phase 4**: 15 tasks ✅
- **Phase 5**: 13 tasks ✅
- **Phase 6**: 9 tasks ✅
- **Phase 7**: 6 tasks ✅
- **MVP Total**: 79 tasks + 4 hotfix = **83 tasks 완료**
- **Tests**: 409 passed, 7 skipped, ruff clean

### Post-MVP (진행 중)
- **Phase A**: 16 tasks (S:6, M:9, L:1) — 16/16 ✅
- **Phase B**: 19 tasks (S:7, M:7, L:3) — 19/19 ✅
- **Phase C**: 12 tasks (S:2, M:8, L:2) — 12/12 ✅
- **Phase C-rev**: 7 tasks (S:1, M:4, L:2) — 7/7 ✅
- **Phase D**: 12 tasks (S:2, M:7, L:2) — 12/12 ✅
- **Phase D-rev**: 13 tasks (S:3, M:7, L:2) — 12/13 ✅ (DR.13 잔여)
- **Phase D-improve**: 7 tasks — 7/7 ✅
- **Phase E**: 10 tasks (S:2, M:3, L:3, XL:1) — 10/10 ✅
- **Phase F**: 10 tasks (S:5, M:4, L:1) — 0/10 📋
- **Phase G~H**: 미정 (각 Phase 진입 시 확정)
- **Post-MVP Phase C~E 파일 영향도**: 신규 ~32 / 수정 ~34 / Migration 0

### Grand Total
- **MVP**: 83 tasks 완료
- **Post-MVP Phase A**: 16/16 ✅
- **Post-MVP Phase B**: 19/19 ✅
- **Post-MVP Phase C**: 12/12 ✅ (상관도 페이지)
- **Post-MVP Phase C-rev**: 7/7 ✅ (피드백 반영)
- **Post-MVP Phase D**: 12/12 ✅ (지표 페이지)
- **Post-MVP Phase D-rev**: 12/13 ✅ (지표 피드백, DR.13 백필 잔여)
- **Post-MVP Phase D-improve**: 7/7 ✅ (지표 추가 개선)
- **Post-MVP Phase E**: 10/10 ✅ (전략 페이지)
- **Post-MVP Phase F**: 0/10 📋 (Agentic Flow)
- **Post-MVP Phase G~H**: 태스크 상세 미확정
