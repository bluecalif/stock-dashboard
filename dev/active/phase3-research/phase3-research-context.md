# Phase 3: Research Engine — Context
> Last Updated: 2026-02-12
> Status: In Progress

## 핵심 파일

### DB 모델 (읽기/쓰기 대상)
- `backend/db/models.py` — FactorDaily, SignalDaily, BacktestRun, BacktestEquityCurve, BacktestTradeLog
- `backend/db/alembic/versions/a5bd6e50f51e_initial_8_tables.py` — 마이그레이션 (변경 불필요)

### 참조 패턴 (collector에서 가져올 것)
- `backend/collector/ingest.py` — `_upsert()` 패턴 (ON CONFLICT DO UPDATE, chunk 처리)
- `backend/config/settings.py` — Settings 싱글턴
- `backend/tests/conftest.py` — 테스트 픽스처 패턴

### 생성할 파일
- `backend/research_engine/preprocessing.py`
- `backend/research_engine/factors.py`
- `backend/research_engine/factor_store.py`
- `backend/research_engine/strategies/__init__.py`
- `backend/research_engine/strategies/base.py`
- `backend/research_engine/strategies/momentum.py`
- `backend/research_engine/strategies/trend.py`
- `backend/research_engine/strategies/mean_reversion.py`
- `backend/research_engine/signal_store.py`
- `backend/research_engine/backtest.py`
- `backend/research_engine/metrics.py`
- `backend/research_engine/backtest_store.py`
- `backend/scripts/run_research.py`
- `backend/tests/unit/test_preprocessing.py`
- `backend/tests/unit/test_factors.py`
- `backend/tests/unit/test_strategies.py`
- `backend/tests/unit/test_backtest.py`
- `backend/tests/unit/test_metrics.py`

## 핵심 결정사항

### 1. 팩터 목록 (15개, masterplan §7.2)
| 카테고리 | 팩터 | 계산 |
|----------|-------|------|
| 수익률 | ret_1d | close.pct_change(1) |
| 수익률 | ret_5d | close.pct_change(5) |
| 수익률 | ret_20d | close.pct_change(20) |
| 수익률 | ret_63d | close.pct_change(63) |
| 추세 | sma_20 | close.rolling(20).mean() |
| 추세 | sma_60 | close.rolling(60).mean() |
| 추세 | sma_120 | close.rolling(120).mean() |
| 추세 | ema_12 | close.ewm(span=12).mean() |
| 추세 | ema_26 | close.ewm(span=26).mean() |
| 추세 | macd | ema_12 - ema_26 |
| 모멘텀 | roc | (close / close.shift(12) - 1) × 100 |
| 모멘텀 | rsi_14 | Wilder RSI(14) |
| 변동성 | vol_20 | ret_1d.rolling(20).std() × √252 |
| 변동성 | atr_14 | ATR(14) |
| 거래량 | vol_zscore_20 | (vol - vol.rolling(20).mean()) / vol.rolling(20).std() |

### 2. 전략 규칙 (masterplan §7.3)
- **모멘텀**: 진입=ret_63d > threshold & vol_20 < cap, 청산=모멘텀 약화 or 변동성 초과
- **추세**: 진입=sma_20 > sma_60 (골든크로스), 청산=sma_20 < sma_60
- **평균회귀**: 진입=가격 z-score 하단 밴드 이탈 후 복귀, 청산=평균 회귀 or 손절

### 3. 공통 체결 규칙
- 신호 발생 **다음 거래일 시가** 체결 (look-ahead bias 방지)
- 수수료/슬리피지 반영 (기본값: 0.1% 편도)
- 포지션: 기본 1배, 현금 비중 허용
- signal: +1(매수), 0(중립), -1(매도)

### 4. 백테스트 모드
- 단일 자산: 자산 1개 × 전략 1개
- 다중 자산: 자산 N개 × 전략 1개 (동일 가중)
- 워크포워드: train/test 구간 분할 지원 (v0에서는 단순 분할)

### 5. 성과 지표 (masterplan §7.5)
- 수익: 누적수익률, CAGR
- 리스크: MDD, 변동성 (연환산)
- 위험조정수익: Sharpe, Sortino, Calmar
- 운용지표: 승률, Turnover
- 벤치마크: Buy & Hold 대비 초과성과

### 6. factor_daily 버전 관리
- `version` 필드: "v1" 기본
- 팩터 로직 변경 시 버전 증가 → 이전 버전 보존
- PK: (asset_id, date, factor_name, version) → 동일 키 UPSERT

## DB 테이블 스키마 참조

```python
# factor_daily PK: (asset_id, date, factor_name, version)
# signal_daily: id(auto), asset_id, date, strategy_id, signal(int), score, action, meta_json
# backtest_run: run_id(uuid), strategy_id, config_json, started_at, ended_at, status
# backtest_equity_curve: (run_id, date), equity, drawdown
# backtest_trade_log: id(auto), run_id, asset_id, entry_date, exit_date, side, pnl, cost
```

## Changed Files

### Step 3.1 (`d476c52`)
- `backend/research_engine/preprocessing.py` — 신규: 전처리 파이프라인
- `backend/tests/unit/test_preprocessing.py` — 신규: 22개 테스트

### Step 3.2-3.3 (`b1ce303`)
- `backend/research_engine/factors.py` — 신규: 15개 팩터 계산
- `backend/tests/unit/test_factors.py` — 신규: 25개 테스트

## Decisions
- [3.1] 크립토는 일별 캘린더, 기타 자산은 영업일 캘린더로 정렬
- [3.1] 결측 ffill + threshold 검증 (기본 5%)
- [3.2-3.3] RSI Wilder smoothing + edge case 처리 (avg_loss=0 → RSI=100, avg_gain=0 → RSI=0)
- [3.2-3.3] 15개 팩터 한 파일(factors.py)에 통합, compute_all_factors()로 일괄 계산

## 참조 문서
- `docs/masterplan-v0.md` §7 (분석 모듈 상세)
- `docs/session-compact.md` (현재 상태)
- `dev/active/phase2-collector/` (Phase 2 패턴 참조)
