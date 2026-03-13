# Session Compact

> Generated: 2026-03-13
> Source: Phase C~E 상세 기획 확정, dev-docs 생성 중

## Goal
Phase C~E (상관도/지표/전략 페이지 완성) 31 Steps 상세 기획 확정 → dev-docs 생성 → 구현 시작

## Completed
- [x] Phase B 전체 완료 (19/19 tasks)
- [x] Phase C~E 통합 계획 확정 (31 Steps, ~54 파일)
- [x] 기존 Phase C(분석)+D(그래프커스텀) → 페이지별 분리: C(상관도), D(지표), E(전략)
- [x] 기존 Phase E(Memory) → F, Phase F(Onboarding) → G로 리네이밍
- [x] project-overall 3개 파일 동기화 완료

## Current State

### Git 상태
- 최신 커밋: `a3c95c1` (master, origin 동기화 완료)
- 변경: dev-docs만 수정 (코드 변경 없음)

### 인프라 상태
- **Railway**: backend + Postgres, OPENAI_API_KEY 설정 완료
  - 공개 URL: `https://backend-production-e5bc.up.railway.app`
- **Vercel**: `https://stock-dashboard-alpha-lilac.vercel.app`

### 테스트 상태
- Backend: 440 passed, 7 skipped, ruff clean
- Frontend: TypeScript 0 errors, Vite build 성공

### OpenAI API Key
- `.env` 파일에 설정 완료 (커밋 제외)
- 키 파일: `C:\Users\User\Work\AI-Engine\각종 API Key_REV0.csv` (line 10, book-process)

## Remaining / TODO
- [ ] Phase C dev-docs 생성 (phaseC-correlation)
- [ ] Phase D dev-docs 생성 (phaseD-indicators)
- [ ] Phase E dev-docs 생성 (phaseE-strategy)
- [ ] Phase C 구현 시작 (C.1 ~ C.11)
- [ ] Phase D 구현 (D.1 ~ D.11)
- [ ] Phase E 구현 (E.1 ~ E.9)

### Phase C: 상관도 페이지 (12 Steps)
| Step | 내용 | 파일 |
|------|------|------|
| C.1 | 상관도 분석 서비스 (그룹핑/유사자산) | `analysis/correlation_analysis.py` 신규 |
| C.2 | 스프레드 분석 서비스 | `analysis/spread_service.py` 신규 |
| C.3 | 해석 규칙 상수 | `analysis/interpretation_rules.py` 신규 |
| C.4 | Tool: analyze_correlation | `llm/tools.py` 수정 |
| C.5 | Tool: get_spread | `llm/tools.py` 수정 |
| C.6 | 하이브리드 응답 기반 | `llm/hybrid/` 디렉토리 신규 |
| C.7 | 하이브리드 → LangGraph 통합 | `llm/graph.py`, `chat_service.py` 수정 |
| C.8 | SSE 확장 + chartActionStore | frontend 수정/신규 |
| C.9 | 상관도 페이지 확장 | `CorrelationPage.tsx` 수정 |
| C.10 | SpreadChart + 넛지 질문 | frontend 신규 |
| C.11 | 관심 종목 설정 | `watchlistStore.ts` 신규 |
| C.12 | **통합 검증** — Backend+Frontend+E2E | 전체 검증 |

### Phase D: 지표 페이지 (12 Steps)
| Step | 내용 | 파일 |
|------|------|------|
| D.1 | 지표 상태 해석 서비스 | `analysis/indicator_analysis.py` 신규 |
| D.2 | 성공률 서비스 ⭐ | `analysis/signal_accuracy_service.py` 신규 |
| D.3 | 예측력 비교 | `analysis/indicator_comparison.py` 신규 |
| D.4 | 분석 REST API | `routers/analysis_router.py` 신규 |
| D.5 | Tool: analyze_indicators | `llm/tools.py` 수정 |
| D.6 | 하이브리드 지표 확장 | `hybrid/templates.py` 수정 |
| D.7 | IndicatorSignalPage 통합 | 신규 페이지 |
| D.8 | 지표 오버레이 차트 | `IndicatorOverlayChart.tsx` 신규 |
| D.9 | 성공률 테이블/차트 | frontend 신규 |
| D.10 | 멀티 지표 설정 | `IndicatorSettingsPanel.tsx` 신규 |
| D.11 | chartActionStore 연결 | `IndicatorSignalPage.tsx` 수정 |
| D.12 | **통합 검증** — Backend+Frontend+E2E | 전체 검증 |

### Phase E: 전략 페이지 (10 Steps)
| Step | 내용 | 파일 |
|------|------|------|
| E.1 | 전략 비교 서비스 | `analysis/strategy_analysis.py` 신규 |
| E.2 | 스토리텔링 서비스 ⭐ | `analysis/storytelling_service.py` 신규 |
| E.3 | Tool: compare_strategies | `llm/tools.py` 수정 |
| E.4 | 하이브리드 전략 확장 | `hybrid/templates.py` 수정 |
| E.5 | 전략 비교 REST API | `analysis_router.py` 수정 |
| E.6 | 전략 설명 카드 | `StrategyDescriptionCard.tsx` 신규 |
| E.7 | 에쿼티 이벤트 마커 ⭐ | `EquityCurveWithEvents.tsx` 신규 |
| E.8 | 기간 설정 + 1억원 시드 | `StrategyPage.tsx` 수정 |
| E.9 | 라우트 최종 정리 | `Sidebar.tsx`, `App.tsx` 수정 |
| E.10 | **통합 검증** — Backend+Frontend+E2E | 전체 검증 |

## Key Decisions
- passlib 제거 → bcrypt 직접 사용 (Phase A)
- **Gemini → OpenAI GPT-5 전환**: Gemini 쿼타 초과 (429) + 결제 문제
- 모델: `gpt-5` (심층모드), `gpt-5-mini` (기본) — 심층모드 토글
- LangGraph 유지 (프레임워크 변경 없음, LLM만 교체)
- SSE: fetch + ReadableStream (EventSource GET 제한)
- Chat UI: 우측 슬라이드 패널 (기존 대시보드 유지)
- **Phase C~E 설계 결정**:
  - 기존 C(분석)+D(그래프커스텀) → **페이지별 분리** (C/D/E)
  - 하이브리드 분류기 = 정규표현식+키워드 (LLM intent 안 씀)
  - 분류 실패 시 LangGraph LLM fallback
  - REST 엔드포인트 추가 (성공률/전략비교용, 페이지 렌더링 겸용)
  - 스토리텔링 = 하드코딩 템플릿+f-string (추상 점수 금지)
  - on-the-fly 경량 백테스트 (DB 저장 안 함)
  - 기존 FactorPage/SignalPage 파일 유지, 라우트만 redirect

## Context
- 다음 세션에서는 답변에 한국어를 사용하세요.
- **통합 계획 파일**: `docs/post-mvp-phaseCD-detail.md`
- **기존 코드 패턴**: Router-Service-Repository 3계층, 함수형 repo, Pydantic v2, SQLAlchemy 2.0 Mapped
- **Railway**: 프로젝트 `stock-dashboard`, CLI 인증 만료 (대시보드에서 직접 설정)
- **Frontend**: React 19 + Vite + TypeScript + Tailwind + axios + react-router-dom v6 + zustand
- **LangGraph**: langgraph 1.1.1 + langchain-openai 1.1.11 + langchain-core 1.2.18
- **SSE 주의**: EventSource(GET) 사용 금지 → fetch + ReadableStream 사용
- **Tool DB 접근**: DI 밖이므로 `next(_get_db())` 패턴 사용
- **재활용 핵심 파일**:
  - `backend/api/services/correlation_service.py` — 상관행렬 계산
  - `backend/api/services/backtest_service.py` — 백테스트 실행
  - `backend/api/services/llm/tools.py` — 현재 5개 Tool
  - `backend/research_engine/factors.py` — 15개 팩터 계산
  - `backend/research_engine/metrics.py` — 성과 지표
  - `backend/research_engine/backtest.py` — 백테스트 엔진

## Project Status

| Phase | 상태 | 비고 |
|-------|------|------|
| MVP (0~7) | ✅ 완료 | 83/83 tasks |
| Post-MVP 기획 | ✅ 완료 | 기술 결정 + 플랜 |
| Phase A Auth | ✅ 완료 | 16/16 tasks |
| Phase B Chatbot | ✅ 완료 | 19/19 tasks |
| Phase C 상관도 | ⬜ 미시작 | 12 Steps, ~22 파일 |
| Phase D 지표 | ⬜ 미시작 | 12 Steps, ~17 파일 |
| Phase E 전략 | ⬜ 미시작 | 10 Steps, ~14 파일 |
| Phase F~G | ⬜ 미시작 | Memory/Onboarding |

## Next Action
1. Phase C~E dev-docs 생성 (`/dev-docs`)
2. Phase C 구현 시작 (C.1 상관도 분석 서비스)
