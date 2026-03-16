# Phase E: 전략 페이지 완성
> Last Updated: 2026-03-16
> Status: In Progress (E.1 완료)
> Source: `docs/post-mvp-feedback.md` Phase E 섹션

## 1. Summary (개요)

**목적**: 3개 전략(모멘텀/역발상/위험회피)의 매매 결과를 시각화하고, 연간 성과 구간 평가 + 이벤트 스토리텔링을 제공
**범위**: 전략 백테스트 서비스, 연간 성과 분석, 스토리텔링, REST 엔드포인트, 프론트 전략 페이지 전면 개편
**예상 결과물**: 신규 ~8 / 수정 ~8 / Migration 0

### 전략 정의 (피드백 기반)

| 전략명 | 기반 지표 | 매매 로직 | 비고 |
|--------|----------|----------|------|
| **모멘텀** | MACD | MACD 시그널 기반 매수/매도 | indicator_signal_service 활용 |
| **역발상** | RSI | RSI 과매수/과매도 기반 매수/매도 | indicator_signal_service 활용 |
| **위험회피** | ATR+vol | 변동성 급등 시 시장 탈출 | 손실 회피 금액 표현 특수 UX |

> **중요 변경**: 기존 research_engine strategies(momentum/trend/mean_reversion)가 아닌 Phase D-rev에서 구축한 `indicator_signal_service`의 on-the-fly 시그널을 활용. 기존 전략은 하위호환 유지하되 전략 페이지 UX는 지표 기반으로 전환.

## 2. Current State (현재 상태)

- Phase D-rev 완료 (12/13, DR.13 백필 잔여) — indicator_signal_service 구축 완료
- Phase D-improve 완료 (7/7) — 시그널 시각구분, 색상 규칙, T+3 frequency 적용
- 전략 페이지: 기존 에쿼티 커브 비교 + 메트릭스 + 거래 이력 (research_engine strategies 기반)
- 백테스트: DB 저장된 결과 조회만 (on-the-fly 비교 없음)
- 스토리텔링/이벤트 마커/연간 성과 없음

## 3. Target State (목표 상태)

- **전략 선택 UI**: 모멘텀/역발상/위험회피 3개 전략 선택 + 명확/간결한 설명 카드
- **에쿼티 커브**: 매수/매도 마커 + Best/Worst 구간 visual annotation
- **연간 성과**: 1년 단위로 전략 적합 구간 vs 부적합 구간 표현
- **수익 금액 시각화**: 기간별 매수/매도 및 수익 금액을 직관적으로 표현 (1억원 시드)
- **위험회피 특수**: 탈출 시 손실 회피 금액 (Buy&Hold 대비 절감액) 명시
- **이벤트 스토리텔링**: 매매 포인트별 내러티브 (효과 큰 구간, 실패 구간 설명)
- **REST**: `POST /v1/analysis/strategy-backtest`
- **라우트 최종 정리**: 5개 항목 (홈/가격/상관/지표시그널/전략)

## 4. Implementation Stages

### Stage A: Backend 전략 백테스트 서비스 (E.1~E.3)

1. **E.1** 전략 백테스트 서비스 — `strategy_backtest_service.py` 신규
   - `run_strategy_backtest(db, asset_id, strategy_name, start, end, initial_cash=100_000_000) → StrategyBacktestResult`
   - strategy_name: "momentum"(MACD), "contrarian"(RSI), "risk_aversion"(ATR+vol)
   - 흐름: indicator_signal_service → 시그널 DataFrame → backtest.run_backtest() → metrics
   - **위험회피 특수 로직**: ATR+vol exit 시그널 → B&H 대비 손실 회피 금액 계산
   - on-the-fly (DB 저장 없음)
   - 테스트: `test_strategy_backtest_service.py`

2. **E.2** 연간 성과 분석 서비스 — `annual_performance_service.py` 신규
   - `compute_annual_performance(equity_curve, trades, strategy_name) → list[AnnualPerformance]`
   - AnnualPerformance: year, return_pct, pnl_amount, mdd, num_trades, win_rate, is_favorable (전략 적합 구간 판별)
   - 1년 단위로 에쿼티 커브 슬라이싱 → 연도별 지표 집계
   - is_favorable 기준: 수익률 > 0 AND win_rate > 50%
   - 테스트: `test_annual_performance.py`

3. **E.3** 이벤트 스토리텔링 서비스 — `storytelling_service.py` 신규
   - `generate_trade_narratives(trades, prices_df, strategy_name) → list[TradeNarrative]`
   - TradeNarrative: entry/exit 날짜·가격, pnl, pnl_pct, holding_days, narrative, is_best, is_worst
   - **Best/Worst 거래 식별**: PnL 기준 상위/하위 거래 마킹
   - 내러티브 규칙: 수익/손실, 장기보유(>60일), 대폭변동(>10%), 위험회피(손실 회피 금액)별 표현
   - `generate_strategy_summary(result, annual_perf) → str` — 전체 요약 + 연간 평가 포함
   - 재활용: `backtest.TradeRecord`
   - 테스트: `test_storytelling.py`

### Stage B: REST + LangGraph (E.4~E.5)

4. **E.4** 전략 백테스트 REST 엔드포인트
   - `analysis_router.py` 수정 — `POST /v1/analysis/strategy-backtest`
   - 요청: asset_id, strategy_name, period (6M/1Y/2Y/3Y), initial_cash
   - 응답: 에쿼티 커브 + 메트릭스 + 거래 이력(내러티브 포함) + 연간 성과 + 요약
   - `schemas/analysis.py` 수정 — StrategyBacktestRequest/Response 추가

5. **E.5** LangGraph Tool + 하이브리드 확장
   - `tools.py` 수정 — `backtest_strategy` Tool 추가
   - `hybrid/templates.py`, `classifier.py` 수정 — 전략 카테고리 확장
   - 카테고리: strategy_explain, strategy_backtest, strategy_compare

### Stage C: Frontend (E.6~E.9)

6. **E.6** 전략 설명 카드 — `strategy/StrategyDescriptionCard.tsx` 신규
   - 3개 전략별 설명 (접힘/펼침)
   - 모멘텀: "MACD 시그널을 따라 추세에 올라타는 전략..."
   - 역발상: "RSI 과매도 구간에서 반등을 노리는 전략..."
   - 위험회피: "ATR+변동성 급등 시 시장을 떠나 손실을 줄이는 전략..."
   - 전략 선택 → API 호출 트리거

7. **E.7** 에쿼티 커브 + 매매 이벤트 마커 ⭐핵심
   - `charts/EquityCurveWithEvents.tsx` 신규
   - ReferenceDot: 매수=초록 마커, 매도=빨강 마커
   - **Best/Worst 구간 annotation**: 효과 가장 큰 거래 + 실패한 거래를 visual하게 표시
     - Best: 초록 하이라이트 영역 + 수익 금액 라벨
     - Worst: 빨강 하이라이트 영역 + 손실 금액 라벨
   - **위험회피 특수**: 탈출 구간에서 B&H 대비 손실 회피 금액 표시
   - 마커 클릭 → 내러티브 패널 표시
   - `strategy/TradeNarrativePanel.tsx` 신규 — 거래별 상세 내러티브 카드
   - 재활용: `EquityCurveChart` 로직

8. **E.8** 연간 성과 차트 + 기간 설정
   - `charts/AnnualPerformanceChart.tsx` 신규 — 연도별 바 차트
     - Y축: 수익률(%) 또는 수익 금액(원)
     - 색상: 적합 구간=초록, 부적합 구간=빨강
     - 각 바에 win_rate, 거래 수 라벨
   - `StrategyPage.tsx` 수정 — 6M/1Y/2Y/3Y 기간 프리셋 + 1억원 시드
   - `api/analysis.ts` 수정 — `fetchStrategyBacktest()` 추가
   - 금액 포맷: `toLocaleString('ko-KR')` + ₩ 접두사

9. **E.9** 라우트 최종 정리
   - `Sidebar.tsx` 수정 — 5개 항목 (홈/가격/상관/지표시그널/전략)
   - `App.tsx` 수정 — `/factors`, `/signals` → `/indicators` redirect 확인
   - 기존 FactorPage.tsx, SignalPage.tsx 파일 유지 (삭제 안 함)

### Stage D: 통합 검증 (E.10)

10. **E.10** Phase E 통합 검증
    - Backend: `ruff check .` clean + `pytest` 전체 통과
    - Frontend: `tsc --noEmit` 0 errors + `vite build` 성공
    - **프로덕션 배포**: `git push` → Railway/Vercel 자동 배포 확인
    - **프로덕션 브라우저 E2E 체크리스트**:
      1. 전략 페이지 렌더링 (3개 전략 선택)
      2. 전략 설명 카드 (접힘/펼침, 전략별 설명)
      3. 에쿼티 커브 매매 마커 (매수=초록, 매도=빨강)
      4. Best/Worst 구간 visual annotation (하이라이트 + 금액 라벨)
      5. 내러티브 패널 (마커 클릭 → 상세 내러티브)
      6. 연간 성과 바 차트 (1년 단위, 적합/부적합 구간 색상)
      7. 기간 설정 (6M/1Y/2Y/3Y) + 1억원 시드 금액 포맷
      8. 위험회피 전략: 손실 회피 금액 표시
      9. 라우트 최종 정리: 5개 항목 네비게이션 + redirect
      10. 챗봇 넛지 질문 (전략 페이지 전용)
    - REST API 프로덕션 확인: `POST /v1/analysis/strategy-backtest`

## 5. Task Breakdown

| # | Task | Size | 의존성 |
|---|------|------|--------|
| E.1 | 전략 백테스트 서비스 | L | indicator_signal_service |
| E.2 | 연간 성과 분석 서비스 | M | E.1 |
| E.3 | 이벤트 스토리텔링 서비스 | L | E.1 |
| E.4 | 전략 백테스트 REST | M | E.1, E.2, E.3 |
| E.5 | Tool + 하이브리드 확장 | M | E.4 |
| E.6 | 전략 설명 카드 | S | - |
| E.7 | 에쿼티 이벤트 마커 + 내러티브 ⭐ | XL | E.4 |
| E.8 | 연간 성과 차트 + 기간 설정 | L | E.4, E.7 |
| E.9 | 라우트 최종 정리 | S | Phase D IndicatorSignalPage |
| E.10 | Phase E 통합 검증 | M | E.1~E.9 전체 |

## 6. Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| indicator 시그널 기반 백테스트가 기존 전략 대비 성과 차이 | 양쪽 결과 비교 검증, 기존 전략 API 하위호환 유지 |
| ATR+vol 위험회피 전략의 손실 회피 계산 복잡도 | B&H equity 대비 차감 방식으로 단순화 |
| Best/Worst 구간 annotation이 과도한 경우 | 상위 1~2건만 표시, 나머지는 내러티브 패널에서 확인 |
| 1년단위 슬라이싱 시 데이터 부족 (최근 연도) | 6개월 이상 데이터가 있는 연도만 표시, 부분연도 라벨 |
| on-the-fly 백테스트 성능 | 3년 데이터 7자산 → ms 단위 (충분히 빠름) |

## 7. Dependencies

**내부**:
- `api/services/analysis/indicator_signal_service.py` — Phase D-rev에서 구축, on-the-fly 시그널 생성
- `research_engine/backtest.py` — 백테스트 엔진 (run_backtest)
- `research_engine/metrics.py` — 성과 지표 (compute_metrics)
- Phase C 하이브리드 기반, Phase D 분석 라우터

**외부 (신규 없음)**: 기존 패키지로 충분
