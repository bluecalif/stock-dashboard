# Phase D: 지표 페이지 완성
> Last Updated: 2026-03-13
> Status: Planning

## 1. Summary (개요)

**목적**: 지표 현재 상태 해석 + 매수/매도 성공률 + 예측력 비교 + REST API + 프론트 통합 페이지 완성
**범위**: 지표 분석 3개 서비스, 분석 REST 라우터, LangGraph Tool 1개, 하이브리드 확장, IndicatorSignalPage 통합, 차트/테이블 컴포넌트
**예상 결과물**: 신규 ~10 / 수정 ~7 / Migration 0

## 2. Current State (현재 상태)

- Phase C 완료 전제: 하이브리드 응답 기반 (`hybrid/`), chartActionStore, SSE ui_action 구축됨
- 팩터/시그널 페이지: 별도 존재 (FactorPage, SignalPage)
- 팩터 데이터: factor_daily 55K+ rows, 15개 팩터
- 시그널 데이터: signal_daily 15K+ rows, 3개 전략
- 성공률/예측력 분석 없음

## 3. Target State (목표 상태)

- 지표 현재 상태 해석: RSI>70 과매수, MACD 양수/음수/교차 등
- 매수/매도 성공률: signal=1 시점 → 5일 후 close 비교
- 예측력 비교: 3개 전략 성공률 순위 정렬
- REST API: `GET /v1/analysis/signal-accuracy`, `GET /v1/analysis/indicator-comparison`
- IndicatorSignalPage: 탭(지표 현황 / 시그널 타임라인 / 성공률)
- 오버레이 차트: 가격 + 선택 지표 (별도 YAxis) + 정규화 토글
- 성공률 테이블/차트: 색상코딩 (60%+ 녹색, 40%- 적색)

## 4. Implementation Stages

### Stage A: Backend 분석 서비스 (D.1~D.3)
1. **D.1** 지표 분석 서비스 — `indicator_analysis.py`
   - `INDICATOR_RULES` 상수 dict
   - `interpret_indicator_state(factor_name, value) → IndicatorState`
   - RSI, MACD, SMA 해석 규칙
   - 테스트: `test_indicator_analysis.py`

2. **D.2** 지표 성공률 서비스 ⭐ — `signal_accuracy_service.py`
   - `compute_signal_accuracy(db, asset_id, strategy_id, forward_days=5) → SignalAccuracyResult`
   - SignalAccuracyResult: buy_success_rate, sell_success_rate, avg_return_after_buy/sell, per_signal_details
   - 로직: signal=1 발생 시점에서 forward_days일 후 close > 시점 close → 성공
   - 재활용: `signal_repo.get_signals()`, `price_repo.get_prices()`
   - 테스트: `test_signal_accuracy.py`

3. **D.3** 지표 간 예측력 비교 — `indicator_comparison.py`
   - `compare_indicator_accuracy(db, asset_id, strategy_ids, forward_days) → list[IndicatorComparisonRow]`
   - 3개 전략 각각의 성공률 비교 → 승률 순위 정렬
   - 재활용: `signal_accuracy_service`
   - 테스트: `test_indicator_comparison.py`

### Stage B: REST API + LangGraph (D.4~D.6)
4. **D.4** 분석 REST 엔드포인트
   - `schemas/analysis.py` — 요청/응답 Pydantic 스키마
   - `routers/analysis_router.py` — GET signal-accuracy, GET indicator-comparison
   - `main.py` 수정 — 라우터 등록
   - 테스트: 엔드포인트 통합 테스트

5. **D.5** Tool — `analyze_indicators`
   - `analyze_indicators(asset_id, factor_names)` → 현재 상태 해석 + 성공률 + 예측력 비교
   - `tools.py` 수정

6. **D.6** 하이브리드 응답 — 지표 카테고리 확장
   - `hybrid/templates.py`, `classifier.py` 수정
   - 카테고리: indicator_explain, signal_accuracy, indicator_compare
   - 넛지: "현재 RSI 상태가 궁금하신가요?", "지표 성공률을 확인해볼까요?"

### Stage C: Frontend 통합 페이지 (D.7~D.9)
7. **D.7** IndicatorSignalPage 통합
   - `pages/IndicatorSignalPage.tsx` 신규
   - 탭: 지표 현황 / 시그널 타임라인 / 성공률
   - 기존 FactorPage + SignalPage 로직 재활용
   - `App.tsx` 수정 — `/indicators` 라우트 + redirect
   - `Sidebar.tsx` 수정 — 네비 통합

8. **D.8** 지표 오버레이 차트
   - `charts/IndicatorOverlayChart.tsx` 신규
   - ComposedChart: 가격(Line) + 선택 지표(Line, 별도 YAxis) + 정규화 토글

9. **D.9** 성공률 테이블/차트
   - `analysis/AccuracyTable.tsx` 신규 — 색상코딩
   - `charts/AccuracyBarChart.tsx` 신규
   - `api/analysis.ts` 신규 — `fetchSignalAccuracy()`, `fetchIndicatorComparison()`

### Stage D: Frontend 고도화 (D.10~D.11)
10. **D.10** 멀티 지표 설정 + 정규화
    - `common/IndicatorSettingsPanel.tsx` 신규
    - 지표 표시/숨기기 토글, 단위 변환, 정규화 모드
    - `IndicatorSignalPage.tsx` 수정 — 설정 패널 연결

11. **D.11** chartActionStore 연결
    - `IndicatorSignalPage.tsx` 수정 — consumeAction 훅
    - 예: `set_filter(factor_name="rsi_14")` → RSI 자동 선택

### Stage E: 통합 검증 (D.12)
12. **D.12** Phase D 통합 검증
    - Backend: `ruff check .` clean + `pytest` 전체 통과
    - Frontend: `tsc --noEmit` 0 errors + `vite build` 성공
    - **프로덕션 배포 (필수)**: `git push` → Railway/Vercel 자동 배포 확인
    - **프로덕션 브라우저 E2E 체크리스트 (필수)**:
      1. IndicatorSignalPage 렌더링 (탭 3개: 지표 현황 / 시그널 / 성공률)
      2. 탭 전환 동작 확인
      3. 오버레이 차트: 가격 + 지표 라인 표시
      4. 성공률 테이블: 색상코딩 (60%+ 녹색, 40%- 적색)
      5. 멀티 지표 설정 패널 동작
      6. chartActionStore 연동 (챗봇 → 지표 자동 선택)
      7. 챗봇 넛지 질문 (indicators 페이지 전용)
      8. 챗봇 하이브리드 응답 (지표 질문 → 템플릿 응답)
    - REST API 프로덕션 확인: `/v1/analysis/signal-accuracy`, `/v1/analysis/indicator-comparison`

## 5. Task Breakdown

| # | Task | Size | 의존성 |
|---|------|------|--------|
| D.1 | 지표 분석 서비스 | M | - |
| D.2 | 성공률 서비스 | L | - |
| D.3 | 예측력 비교 | M | D.2 |
| D.4 | REST 엔드포인트 | M | D.1, D.2, D.3 |
| D.5 | Tool: analyze_indicators | M | D.1, D.2 |
| D.6 | 하이브리드 지표 확장 | S | Phase C 하이브리드 기반 |
| D.7 | IndicatorSignalPage | L | D.4 |
| D.8 | 오버레이 차트 | M | D.7 |
| D.9 | 성공률 테이블/차트 | M | D.4, D.7 |
| D.10 | 멀티 지표 설정 | M | D.8 |
| D.11 | chartActionStore 연결 | S | Phase C chartActionStore |
| D.12 | Phase D 통합 검증 | M | D.1~D.11 전체 |

## 6. Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| 성공률 계산 시 데이터 부족 (신호 적은 전략) | 최소 신호 수 임계값 설정, 부족 시 "데이터 불충분" 표시 |
| forward_days 범위에 데이터 없는 경우 | 해당 신호 제외, 유효 신호 수 표시 |
| FactorPage/SignalPage → IndicatorSignalPage 리다이렉트 혼란 | 기존 파일 유지, 라우트만 redirect |

## 7. Dependencies

**내부**:
- Phase C 하이브리드 기반 (`hybrid/` 디렉토리, chartActionStore)
- `signal_repo.get_signals()`, `price_repo.get_prices()`
- `factor_repo.get_factors()` — 팩터 조회

**외부 (신규 없음)**: 기존 패키지로 충분
