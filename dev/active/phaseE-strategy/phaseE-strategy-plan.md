# Phase E: 전략 페이지 완성
> Last Updated: 2026-03-13
> Status: Planning

## 1. Summary (개요)

**목적**: 전략 비교 분석 + 이벤트 스토리텔링 + 에쿼티 이벤트 마커 + 기간 설정 + 라우트 최종 정리
**범위**: 전략 비교 서비스, 스토리텔링 서비스, LangGraph Tool 1개, 하이브리드 확장, REST 엔드포인트, 프론트 전략 페이지 고도화
**예상 결과물**: 신규 ~7 / 수정 ~7 / Migration 0

## 2. Current State (현재 상태)

- Phase C+D 완료 전제: 하이브리드 응답, chartActionStore, 분석 REST 라우터, IndicatorSignalPage
- 전략 페이지: 에쿼티 커브 비교 + 메트릭스 카드 + 거래 이력 테이블
- 백테스트: DB 저장된 결과 조회만 (on-the-fly 비교 없음)
- 스토리텔링/이벤트 마커 없음

## 3. Target State (목표 상태)

- 전략 비교: on-the-fly 경량 백테스트 (DB 저장 안 함), 6M/1Y/2Y 기간
- 이벤트 스토리텔링: 매매 포인트별 내러티브 (하드코딩 템플릿+f-string)
- 에쿼티 이벤트 마커: ReferenceDot로 매매 포인트 표시
- 내러티브 패널: 마커 클릭 시 상세 내러티브 카드
- REST: `POST /v1/analysis/strategy-comparison`
- 전략 설명 카드: 3개 전략별 설명 (접힘/펼침)
- 라우트 최종 정리: 5개 항목 (홈/가격/상관/지표시그널/전략)

## 4. Implementation Stages

### Stage A: Backend 분석 서비스 (E.1~E.2)
1. **E.1** 전략 비교 분석 서비스 — `strategy_analysis.py`
   - `compare_strategies(db, asset_id, strategy_ids, start, end, initial_cash=100_000_000) → StrategyComparisonResult`
   - on-the-fly 경량 백테스트: `run_backtest()` + `compute_metrics()` 직접 호출
   - 재활용: `research_engine/backtest.py`, `research_engine/metrics.py`, `strategies/`
   - 테스트: `test_strategy_analysis.py`

2. **E.2** 이벤트 스토리텔링 서비스 ⭐ — `storytelling_service.py`
   - `generate_trade_narratives(trades, prices_df, strategy_id) → list[TradeNarrative]`
   - TradeNarrative: entry/exit 날짜·가격, pnl, holding_days, narrative
   - 내러티브 규칙: 수익/손실, 장기보유(>60일), 대폭변동(>10%)별 다른 표현
   - `generate_strategy_story(result) → str` — 전체 요약 내러티브
   - 재활용: `backtest.TradeRecord`
   - 테스트: `test_storytelling.py`

### Stage B: LangGraph + REST (E.3~E.5)
3. **E.3** Tool — `compare_strategies`
   - `compare_strategies(asset_id, strategy_ids, period)` → 에쿼티+메트릭스+내러티브 JSON
   - period(6M/1Y/2Y) → start_date 변환
   - `tools.py` 수정

4. **E.4** 하이브리드 응답 — 전략 카테고리 확장
   - `hybrid/templates.py`, `classifier.py` 수정
   - 카테고리: strategy_explain, strategy_compare, trade_story, backtest_run
   - 전략 설명 하드코딩 (모멘텀="달리는 말에 타는 전략…")

5. **E.5** 전략 비교 REST 엔드포인트
   - `analysis_router.py` 수정 — `POST /v1/analysis/strategy-comparison`
   - `schemas/analysis.py` 수정 — 요청/응답 스키마 추가

### Stage C: Frontend (E.6~E.9)
6. **E.6** 전략 사전 설명 카드
   - `strategy/StrategyDescriptionCard.tsx` 신규
   - 3개 전략별 설명 (접힘/펼침)
   - `StrategyPage.tsx` 수정 — 상단에 설명 카드

7. **E.7** 에쿼티 커브 이벤트 마커 + 내러티브 ⭐
   - `charts/EquityCurveWithEvents.tsx` 신규 — ReferenceDot로 매매 포인트
   - `strategy/TradeNarrativePanel.tsx` 신규 — 클릭 시 내러티브 카드
   - `StrategyPage.tsx` 수정 — 기존 차트 교체
   - 재활용: `EquityCurveChart` 로직

8. **E.8** 기간 설정 + 1억원 시드
   - `StrategyPage.tsx` 수정 — 6M/1Y/2Y 프리셋 + 금액 포맷
   - `api/analysis.ts` 수정 — `fetchStrategyComparison()` 추가

9. **E.9** 라우트 최종 정리
   - `Sidebar.tsx` 수정 — 5개 항목 (홈/가격/상관/지표시그널/전략)
   - `App.tsx` 수정 — `/factors`, `/signals` → `/indicators` redirect 확인
   - 기존 FactorPage.tsx, SignalPage.tsx 파일 유지 (삭제 안 함)

### Stage D: 통합 검증 (E.10)
10. **E.10** Phase E 통합 검증
    - Backend: `pytest` 전체 통과 + `ruff check` clean
    - Frontend: `tsc --noEmit` 0 errors + `vite build` 성공
    - 브라우저 E2E: 전략 페이지 렌더링, 전략 설명 카드, 에쿼티 이벤트 마커, 내러티브 패널, 기간 설정, 1억원 시드 포맷
    - REST API: `POST /v1/analysis/strategy-comparison` 정상 응답
    - 챗봇: 전략 관련 질문 → 하이브리드 응답 + Tool 호출 정상 동작
    - 라우트: 5개 항목 네비게이션, redirect 정상 동작
    - Railway/Vercel 배포 확인 (선택)

## 5. Task Breakdown

| # | Task | Size | 의존성 |
|---|------|------|--------|
| E.1 | 전략 비교 서비스 | L | - |
| E.2 | 스토리텔링 서비스 | L | E.1 |
| E.3 | Tool: compare_strategies | M | E.1, E.2 |
| E.4 | 하이브리드 전략 확장 | S | Phase C 하이브리드 기반 |
| E.5 | 전략 비교 REST | M | E.1 |
| E.6 | 전략 설명 카드 | S | - |
| E.7 | 에쿼티 이벤트 마커 | L | E.5 |
| E.8 | 기간 설정 + 1억원 시드 | M | E.5, E.7 |
| E.9 | 라우트 최종 정리 | S | Phase D IndicatorSignalPage |
| E.10 | Phase E 통합 검증 | M | E.1~E.9 전체 |

## 6. Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| on-the-fly 백테스트 성능 (대량 데이터) | 3년 데이터 7자산 → 충분히 빠름 (ms 단위) |
| 내러티브 템플릿 자연스러움 부족 | 규칙별 다양한 표현 준비, 이후 LLM 보강 가능 |
| 기간 변경 시 UI 깜빡임 | 로딩 상태 + 스켈레톤 UI |

## 7. Dependencies

**내부**:
- `research_engine/backtest.py` — 백테스트 엔진
- `research_engine/metrics.py` — 성과 지표
- `research_engine/strategies/` — 3종 전략
- Phase C 하이브리드 기반, Phase D 분석 라우터

**외부 (신규 없음)**: 기존 패키지로 충분
