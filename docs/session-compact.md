# Session Compact

> Generated: 2026-03-15
> Source: Phase D — D.3~D.6 백엔드 서비스 + API + LangGraph Tool + 하이브리드 응답 완료

## Goal
Phase D 지표 페이지 완성 — D.1~D.12 중 백엔드 분석 서비스(D.1~D.3), REST API(D.4), LangGraph Tool(D.5), 하이브리드 응답 확장(D.6) 구현

## Completed
- [x] D.1 지표 분석 서비스 — `indicator_analysis.py` (RSI/MACD/ATR/vol_20 해석) — `d0392b6`
- [x] D.2 지표 성공률 서비스 — `signal_accuracy_service.py` (매수/매도 성공률) — `d7c829b`
- [x] D.3 지표 간 예측력 비교 — `indicator_comparison.py` (3전략 승률 순위 정렬) — 미커밋
- [x] D.4 분석 REST 엔드포인트 — `routers/analysis.py` + `schemas/analysis.py` — 미커밋
  - `GET /v1/analysis/signal-accuracy` — 특정 자산+전략 성공률
  - `GET /v1/analysis/indicator-comparison` — 3전략 예측력 비교
- [x] D.5 LangGraph Tool — `analyze_indicators` 도구 추가 (현재 상태 + 성공률 + 비교) — 미커밋
- [x] D.6 하이브리드 응답 지표 카테고리 확장 — 미커밋
  - `classifier.py`: 지표 패턴 9개 (INDICATOR_EXPLAIN, SIGNAL_ACCURACY, INDICATOR_COMPARE)
  - `templates.py`: 지표 해석 / 성공률 / 예측력 비교 템플릿 3개
  - `chat_service.py`: `_fetch_hybrid_data`에 지표 카테고리 분기 + indicators 기본 카테고리 설정
  - 넛지 질문 3개는 기존 정의 재활용 (이전 세션에서 추가 완료)

## Current State

### Git 상태
- 최신 커밋: `d7c829b` (master, D.2까지 push 완료)
- 미커밋 변경: D.3~D.6 관련 신규/수정 파일 + dev-docs

### 테스트 상태
- 전체: **647 tests** passed, 7 skipped (561 → 647, +86)
- ruff clean
- 신규 테스트 파일:
  - `tests/unit/test_indicator_comparison.py` — 9개
  - `tests/unit/test_api/test_analysis_router.py` — 7개
  - `tests/unit/test_hybrid_classifier.py` — 기존 33 → 52개 (+19)

### Changed Files (미커밋)
- `backend/api/services/analysis/indicator_comparison.py` — 신규 (D.3)
- `backend/api/schemas/analysis.py` — 신규 (D.4)
- `backend/api/routers/analysis.py` — 신규 (D.4)
- `backend/api/main.py` — 수정 (analysis 라우터 등록)
- `backend/api/services/llm/tools.py` — 수정 (analyze_indicators 도구 추가)
- `backend/api/services/llm/hybrid/classifier.py` — 수정 (지표 패턴 9개)
- `backend/api/services/llm/hybrid/templates.py` — 수정 (지표 템플릿 3개 + 레지스트리)
- `backend/api/services/chat/chat_service.py` — 수정 (_fetch_hybrid_data 지표 분기)
- `backend/tests/unit/test_indicator_comparison.py` — 신규
- `backend/tests/unit/test_api/test_analysis_router.py` — 신규
- `backend/tests/unit/test_hybrid_classifier.py` — 수정

### 인프라 상태
- **Railway**: `https://backend-production-e5bc.up.railway.app`
- **Vercel**: `https://stock-dashboard-alpha-lilac.vercel.app`

## Remaining / TODO
- [ ] D.3~D.6 커밋 (미커밋 상태)
- [ ] D.7 IndicatorSignalPage 통합 (프론트엔드 탭 페이지)
- [ ] D.8 지표 오버레이 차트
- [ ] D.9 성공률 테이블/차트
- [ ] D.10 멀티 지표 설정 + 정규화
- [ ] D.11 chartActionStore 연결
- [ ] D.12 Phase D 통합 검증 + 배포
- [ ] Phase E 구현 (E.1~E.9) — 전략 페이지 완성

## Key Decisions
- **예측력 순위**: 매수/매도 성공률 평균으로 composite score 계산 → 내림차순 정렬
- **부족 데이터 순위**: insufficient_data 전략은 score -1.0으로 하위 배치
- **analyze_indicators 도구**: 3가지 분석(해석 + 성공률 + 비교)을 한 번에 반환하여 Tool 호출 최소화
- **하이브리드 지표 데이터**: 3개 카테고리 모두 동일한 analyze_indicators 도구 호출 → 필요한 필드만 템플릿에서 사용
- **indicators 기본 카테고리**: INDICATOR_EXPLAIN (넛지 분류 실패 시 fallback)
- **forward_days 기본값**: 5거래일 (API에서 1~60 범위)

## Context
- 다음 세션에서는 답변에 한국어를 사용하세요.
- **기존 코드 패턴**: Router-Service-Repository 3계층, 함수형 repo, Pydantic v2, SQLAlchemy 2.0 Mapped
- **Frontend**: React 19 + Vite + TypeScript + Tailwind + axios + react-router-dom v6 + zustand + Recharts
- **LangGraph**: langgraph 1.1.1 + langchain-openai 1.1.11 + langchain-core 1.2.18
- **SSE 주의**: EventSource(GET) 사용 금지 → fetch + ReadableStream 사용
- **LangSmith API Key**: 환경변수 참조 (`.env` 또는 Railway Variables)
- **Phase D 계획**: `dev/active/phaseD-indicators/phaseD-indicators-plan.md`
- **기존 페이지**: FactorPage(`/factors`), SignalPage(`/signals`) — D.7에서 IndicatorSignalPage로 통합

## Project Status

| Phase | 상태 | 비고 |
|-------|------|------|
| MVP (0~7) | ✅ 완료 | 83/83 tasks |
| Phase A Auth | ✅ 완료 | 16/16 tasks |
| Phase B Chatbot | ✅ 완료 | 19/19 tasks |
| Phase C 상관도 | ✅ 완료 | 12/12 Steps |
| Phase C-rev 피드백 | ✅ 완료 | 7/7 Tasks |
| Phase C-rev2 피드백 | ✅ 완료 | 4/4 Tasks + 품질 개선 |
| Phase D 지표 | 🔄 진행 중 | 6/12 Tasks (D.1~D.6 완료) |
| Phase E 전략 | ⬜ 미시작 | 9 Steps |
| Phase F~G | ⬜ 미시작 | Memory/Onboarding |

## Next Action
1. D.3~D.6 변경사항 커밋
2. **D.7** IndicatorSignalPage 통합 (프론트엔드 탭 페이지: 지표 현황 / 시그널 타임라인 / 성공률)
