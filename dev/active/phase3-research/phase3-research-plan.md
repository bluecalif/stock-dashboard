# Phase 3: Research Engine
> Last Updated: 2026-02-12
> Status: In Progress
> Current Step: 3.7 (Stage A+B 완료)

## 1. Summary (개요)

**목적**: DB에 저장된 price_daily 데이터를 기반으로 팩터 생성, 전략 신호 산출, 백테스트 실행까지의 분석 파이프라인을 구축한다.

**범위**: 마스터플랜 §7 (분석 모듈 상세) 전체
- §7.1 전처리 (캘린더 정렬, 결측 처리, 이상치 플래그)
- §7.2 팩터 생성 (15개 팩터)
- §7.3 전략 엔진 (모멘텀/추세/평균회귀 3종)
- §7.4 백테스트 (단일/다중 자산, 워크포워드)
- §7.5 성과 평가 지표 (Sharpe, MDD, CAGR 등)

**예상 결과물**: `backend/research_engine/` 패키지 완성, factor_daily/signal_daily/backtest_* 테이블 활용, 분석 배치 스크립트

## 2. Current State (현재 상태)

### 존재하는 것
- `research_engine/__init__.py` — 빈 패키지 (코드 없음)
- DB 테이블 정의 완료: `factor_daily`, `signal_daily`, `backtest_run`, `backtest_equity_curve`, `backtest_trade_log` (models.py)
- Alembic 마이그레이션 완료: 8개 테이블 생성 (`a5bd6e50f51e`)
- `price_daily` 데이터: 5,559 rows (2023-02 ~ 2026-02), 7개 자산
- pandas, numpy 의존성 설치됨

### 없는 것
- 전처리 로직
- 팩터 계산 코드
- 전략 클래스
- 백테스트 엔진
- 성과 지표 계산
- 분석 배치 스크립트
- 테스트 (research_engine 관련)

## 3. Target State (목표 상태)

```
backend/research_engine/
├── __init__.py
├── preprocessing.py      # 캘린더 정렬, 결측 처리, 이상치 플래그
├── factors.py            # 15개 팩터 계산
├── factor_store.py       # factor_daily UPSERT
├── strategies/
│   ├── __init__.py
│   ├── base.py           # Strategy ABC + 공통 체결 규칙
│   ├── momentum.py       # 모멘텀 전략
│   ├── trend.py          # 추세 전략 (골든/데드크로스)
│   └── mean_reversion.py # 평균회귀 전략
├── signal_store.py       # signal_daily UPSERT
├── backtest.py           # 백테스트 엔진
├── metrics.py            # 성과 평가 지표
└── backtest_store.py     # backtest_* 테이블 저장

backend/scripts/
└── run_research.py       # 분석 배치 스크립트 (팩터→신호→백테스트)

backend/tests/unit/
├── test_preprocessing.py
├── test_factors.py
├── test_strategies.py
├── test_backtest.py
└── test_metrics.py
```

완료 후:
- 7개 자산 × 15개 팩터 = factor_daily에 적재
- 3종 전략 시그널 = signal_daily에 적재
- 백테스트 실행 및 결과 저장 가능
- `scripts/run_research.py`로 일괄 실행

## 4. Implementation Stages (구현 단계)

### Stage A: 전처리 + 팩터 (Task 3.1 ~ 3.4)
- 목표: price_daily → DataFrame 로드 → 팩터 계산 → factor_daily 저장
- 산출물: preprocessing.py, factors.py, factor_store.py + 테스트

### Stage B: 전략 엔진 (Task 3.5 ~ 3.8)
- 목표: 팩터 기반으로 3종 전략 신호 생성 → signal_daily 저장
- 산출물: strategies/ 패키지 + signal_store.py + 테스트

### Stage C: 백테스트 + 성과 (Task 3.9 ~ 3.11)
- 목표: 시그널 기반 백테스트 실행 → 성과 지표 산출 → DB 저장
- 산출물: backtest.py, metrics.py, backtest_store.py + 테스트

### Stage D: 통합 + 배치 (Task 3.12)
- 목표: 전체 파이프라인 통합 배치 스크립트 + 통합 테스트
- 산출물: scripts/run_research.py + 통합 테스트

## 5. Task Breakdown (태스크 목록)

### Stage A: 전처리 + 팩터

| Task | 설명 | Size | 의존성 |
|------|------|------|--------|
| 3.1 | 전처리 파이프라인 — price_daily 로드, 캘린더 정렬, 결측 처리, 이상치 플래그 | M | Phase 2 완료 |
| 3.2 | 수익률 + 추세 팩터 — ret_1d/5d/20d/63d, sma_20/60/120, ema_12/26, macd | M | 3.1 |
| 3.3 | 모멘텀 + 변동성 + 거래량 팩터 — roc, rsi_14, vol_20, atr_14, vol_zscore_20 | M | 3.1 |
| 3.4 | 팩터 DB 저장 — factor_daily UPSERT + 팩터 계산 오케스트레이션 | M | 3.2, 3.3 |

### Stage B: 전략 엔진

| Task | 설명 | Size | 의존성 |
|------|------|------|--------|
| 3.5 | 전략 프레임워크 — Strategy ABC, 공통 체결 규칙 (다음 거래일 시가, 수수료/슬리피지) | M | 3.4 |
| 3.6 | 3종 전략 구현 — 모멘텀, 추세(골든크로스), 평균회귀 | M | 3.5 |
| 3.7 | 시그널 생성 + DB 저장 — signal_daily UPSERT, 시그널 오케스트레이션 | S | 3.6 |

### Stage C: 백테스트 + 성과

| Task | 설명 | Size | 의존성 |
|------|------|------|--------|
| 3.8 | 백테스트 엔진 — 단일/다중 자산, equity curve, trade log 생성 | L | 3.7 |
| 3.9 | 성과 평가 지표 — CAGR, MDD, Sharpe, Sortino, Calmar, 승률, B&H 비교 | M | 3.8 |
| 3.10 | 백테스트 결과 DB 저장 — backtest_run/equity_curve/trade_log 저장 | S | 3.9 |

### Stage D: 통합

| Task | 설명 | Size | 의존성 |
|------|------|------|--------|
| 3.11 | 분석 배치 스크립트 + 통합 테스트 — run_research.py, E2E 테스트 | M | 3.10 |
| 3.12 | dev-docs 갱신 + session-compact 업데이트 | S | 3.11 |

**총계**: 12 Tasks (S: 3, M: 7, L: 1, XL: 0)

## 6. Risks & Mitigation (리스크 및 완화)

| 리스크 | 영향 | 완화 |
|--------|------|------|
| 팩터 계산 시 데이터 부족 (120일 SMA 등) | 초기 구간 NaN | 최소 데이터 요구량 검증 + NaN 전파 정책 명확화 |
| 전략 로직 오류 (미래 데이터 참조) | 백테스트 신뢰성 저하 | 시점 기준 strict 검증, look-ahead bias 방지 테스트 |
| 백테스트 성능 (대량 데이터) | 실행 시간 증가 | vectorized pandas 연산 우선, 루프 최소화 |
| DB 부하 (factor_daily 대량 INSERT) | Railway 쿼터 | 배치 UPSERT + chunk 처리 (collector 패턴 재활용) |

## 7. Dependencies (의존성)

### 내부
- `db.models`: FactorDaily, SignalDaily, BacktestRun, BacktestEquityCurve, BacktestTradeLog
- `config.settings`: DATABASE_URL
- `collector.ingest._upsert` 패턴 참조 (UPSERT 구현)

### 외부 (이미 설치됨)
- `pandas >= 2.0`: DataFrame 연산, 팩터 계산
- `numpy`: 수학 연산
- `sqlalchemy >= 2.0`: DB 접근

### 컨벤션 체크
- [x] OHLCV 표준 스키마 준수 (price_daily 읽기)
- [x] factor_daily PK: (asset_id, date, factor_name, version)
- [x] idempotent UPSERT (factor/signal 저장)
- [x] 팩터 계산 정확성 테스트 (고정 샘플)
- [x] look-ahead bias 방지 (전략/백테스트)
