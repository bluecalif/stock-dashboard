# Phase 3: Research Engine — Tasks
> Last Updated: 2026-02-12
> Status: In Progress

## Progress: 7/12 (58%)

---

### Stage A: 전처리 + 팩터

- [x] **3.1** 전처리 파이프라인 `[M]` — `d476c52`
  - preprocessing.py: price_daily → DataFrame 로드 함수
  - 캘린더 정렬 (영업일 기준, 크립토는 전일)
  - 결측 처리 (허용 임계치 초과 시 실패)
  - 이상치 플래그 생성
  - test_preprocessing.py (최소 8개 테스트)

- [x] **3.2** 수익률 + 추세 팩터 `[M]` — `b1ce303`
  - factors.py: 수익률 (ret_1d, ret_5d, ret_20d, ret_63d)
  - factors.py: 추세 (sma_20, sma_60, sma_120, ema_12, ema_26, macd)
  - 고정 샘플 데이터로 정확성 검증
  - test_factors.py (수익률 + 추세 부분, 최소 10개)

- [x] **3.3** 모멘텀 + 변동성 + 거래량 팩터 `[M]` — `b1ce303`
  - factors.py: 모멘텀 (roc, rsi_14)
  - factors.py: 변동성 (vol_20, atr_14)
  - factors.py: 거래량 (vol_zscore_20)
  - RSI Wilder 방식 정확성 검증
  - test_factors.py (모멘텀+변동성+거래량, 최소 8개)

- [x] **3.4** 팩터 DB 저장 `[M]` — `1e35fd9`
  - factor_store.py: factor_daily UPSERT (collector 패턴 재활용)
  - 팩터 계산 오케스트레이션 (전 자산 × 전 팩터)
  - version 관리 ("v1")
  - 테스트 16개 (UPSERT, 오케스트레이션, 에러 핸들링)

---

### Stage B: 전략 엔진

- [x] **3.5** 전략 프레임워크 `[M]` — `6956015`
  - strategies/base.py: Strategy ABC, SignalResult dataclass
  - generate_signals(): next-day execution, action labeling
  - strategies/__init__.py: STRATEGY_REGISTRY + get_strategy()
  - test_strategies.py (24개 테스트)

- [x] **3.6** 3종 전략 구현 `[M]` — `6956015`
  - strategies/momentum.py: ret_63d > threshold & vol_20 < cap
  - strategies/trend.py: sma_20 > sma_60 골든/데드크로스
  - strategies/mean_reversion.py: z-score 밴드 이탈/복귀 + stop-loss
  - 전략별 상태머신, long-only (+1/0)

- [x] **3.7** 시그널 생성 + DB 저장 `[S]` — `6956015`
  - signal_store.py: DELETE+INSERT 패턴 (idempotent)
  - store_signals_for_asset, store_signals_all 오케스트레이션
  - test_signal_store.py (19개 테스트)

---

### Stage C: 백테스트 + 성과

- [ ] **3.8** 백테스트 엔진 `[L]`
  - backtest.py: BacktestEngine 클래스
    - 단일 자산 백테스트
    - equity curve 생성
    - trade log 생성
    - 수수료/슬리피지 반영
  - 다중 자산 모드 (동일 가중)
  - look-ahead bias 방지 검증
  - test_backtest.py (최소 10개)

- [ ] **3.9** 성과 평가 지표 `[M]`
  - metrics.py: 지표 계산 함수
    - 누적수익률, CAGR, MDD
    - 변동성 (연환산)
    - Sharpe, Sortino, Calmar
    - 승률, Turnover
    - Buy & Hold 비교
  - test_metrics.py (고정 값 검증, 최소 8개)

- [ ] **3.10** 백테스트 결과 DB 저장 `[S]`
  - backtest_store.py: backtest_run, equity_curve, trade_log 저장
  - status 관리 (running → success/failure)
  - 테스트

---

### Stage D: 통합

- [ ] **3.11** 분석 배치 스크립트 + 통합 테스트 `[M]`
  - scripts/run_research.py: CLI 스크립트
    - 전처리 → 팩터 생성 → 시그널 생성 → 백테스트 실행
    - --assets, --strategy, --start, --end 인자
    - daily_collect.bat에 후속 실행 연동
  - 통합 테스트 (DB → 팩터 → 시그널 → 백테스트 E2E)

- [ ] **3.12** dev-docs + session-compact 갱신 `[S]`
  - phase3-research-tasks.md 완료 마킹
  - session-compact.md 업데이트
  - Phase 4 준비 안내

---

## Summary
- **Total**: 12 tasks
- **Size**: S(3) + M(7) + L(1) = 12
- **Estimated test count**: ~60+
