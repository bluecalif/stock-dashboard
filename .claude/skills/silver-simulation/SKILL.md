---
name: silver-simulation
description: Stock Dashboard Silver gen 시뮬레이션 엔진 도메인 가이드. 적립식 replay, 전략 A/B (lock 사이클 / 365일 강제 재매수 / 12개월 grace), 포트폴리오 60/20/20 + 연 1회 리밸런싱, WBI synthetic GBM (시드 42, KRW), cyclic returns padding, USD↔KRW 환산, 캘린더 연도 MDD, 21개 D-lock 결정. 사용자가 silver/simulation/replay/strategy/portfolio/WBI/padding/MDD/적립식/fx_daily/Tab A/B/C 같은 단어를 쓰거나, /silver/compare 페이지·`backend/research_engine/simulation/` 모듈·`/v1/silver/simulate/*` 라우터를 작업할 때 반드시 활성화. 백테스트(`backtest_*`)와 의미가 다른 별개 엔진이므로, 이전 Bronze 백테스트 패턴으로 추론하지 말고 이 skill을 우선 참조할 것.
---

# Silver Simulation Engine — Domain Guide

## Purpose

Stock Dashboard **Silver gen**의 시뮬레이션 엔진(`backend/research_engine/simulation/`)을 설계·구현·디버그할 때 매번 참조하는 lock 규칙과 함정 모음. Bronze gen의 백테스트(`backtest_run`/`backtest_equity_curve`/`backtest_trade_log`)는 Phase 4에서 drop되며, Silver의 simulation은 **다른 의미**의 엔진이다 — 사용자(초보 투자자)가 적립식 비교를 통해 자산/전략/포트폴리오 의사결정을 하기 위한 도구.

**단일 source of truth**: `docs/silver-masterplan.md` §2~§3 + `dev/active/project-overall/project-overall-context.md` §3 (D-1~D-21).

## When to Use

이 skill은 다음 작업을 시작할 때 **반드시 먼저 읽고**, 결정 사항을 인용하면서 코딩한다:

- `backend/research_engine/simulation/` 신규 파일 작성 (8 모듈)
- `routers/simulation.py` / `routers/fx.py` 신규 작성
- 적립식 replay / 전략 A·B / 포트폴리오 알고리즘 구현·수정
- padding / WBI / fx / MDD 산식 구현·수정
- KPI 4종 (최종자산 / 총수익률 / 연환산 / 캘린더 연도 MDD) 산출
- silver-rev1-phase2 진행 중 lock 규칙 의문 발생 시
- Phase 4 빅뱅 cut-over 시 `simulation_*` Agentic tool 등록 시 (의미 재확인)

**활성화 안 해도 되는 경우**: Bronze gen 영역(SOXL/금/은 운영, 기존 backtest 운영) — 이건 `backend-dev`로 충분.

---

## 21 D-Lock 결정 (코딩 시 매번 확인)

> 본 표는 `dev/active/project-overall/project-overall-context.md` §3과 동일. 결정 위반은 silver-rev1 핵심 기능을 깨뜨리므로 함부로 추론하지 말고 이 표를 인용한다. 구현 함수에 `# D-N` 주석으로 결정 ID를 남기면 추후 추적 가능.

| # | 결정 | 출처 | 코딩 위치 |
|---|---|---|---|
| D-1 | JEPY → **JEPI** 통일 (JPMorgan, ~5년 history) | Q1-1 | `SYMBOL_MAP`, `asset_master.display_name` |
| D-2 | history 부족 시 **일별 수익률 cyclic 복제** (가격 점프 X) | Q1-2 | `padding.py` |
| D-3 | USD/KRW 신규 테이블 `fx_daily` (FDR `USD/KRW` 10년) | Q1-3 | Phase 1 migration + `fx_collector.py` |
| D-4 | 배당 = 공시 연 배당률 / 252 균등 분할, 매 거래일 보유분에 (1+rate) 적용 | Q1-4 | `replay.py` 배당 재투자 |
| D-5 | WBI (Warren Buffett Index) = 거래일 등비 + GBM(σ=1%/일, drift 보정 `μ-σ²/2`), 시드 42, **KRW 자산** | Q2-5/6 | `wbi.py` reproducibility 보장 |
| D-6 | 트리거 통화 = **현지통화 가격 기준** (USD 자산은 USD 가격으로 ratio 판정) | Q3-9 | `strategy_a.py`, `strategy_b.py` |
| D-7 | 전략 A 강제 재매수 = **매도일 + 365일** (draft "12월 마지막 거래일" 폐기) | Q4-11 | `strategy_a.py` `forced = date >= sell_date + timedelta(days=365)` |
| D-8 | 전략 A lock = **매도해 ~ 재매수해 (포함)**, 페어 완성 후 같은 해 매도 시그널 무시 | Q4-13 | `strategy_a.py` `lock_until_year` state |
| D-9 | 전략 A grace = **12개월** (적립식 시작 후 첫 12개월 매도 트리거 무시) | Q4-14 | `strategy_a.py` `grace_end = period_start + relativedelta(months=12)` |
| D-10 | 급등 조건 = **`오늘종가 / 60거래일 전 종가 ≥ 1.20`** | Q4-10 | `strategy_a.py` 60거래일 lookback ratio |
| D-11 | MDD = **캘린더 연도** 기준 (Jan-Dec 슬라이스 후 최악) | Q5-15 | `mdd.py` |
| D-12 | UI = 상단 가로 nav + `+` 버튼 drawer + 모바일 필수 | Q6-16/18/20 | (frontend) |
| D-13 | chat/AI = Bronze Phase F 그대로 유지 | Q6-19 | `simulation_*` tool 추가만 |
| D-14 | 신호 카드 = 개별 RSI/MACD/ATR + 상태 라벨 (종합 점수 X) | Q7-21 | (frontend) |
| D-15 | Bronze→Silver = **빅뱅 교체** (사용자 1명, 다운타임 0 영향) | Q8-24 | Phase 4 cut-over |
| D-16 | StrategyPage drop = **DB 테이블도 drop** (`backtest_run/equity_curve/trade_log`) | Q8-26 | Phase 4 migration |
| D-17 | 이벤트 순서 lock = **정기 적립 후 조건 실행** (같은 날 겹치면 적립 먼저) | §1.1 | `replay.py` 적립 → `strategy.step()` 순서 |
| D-18 | KPI 4종 = 최종자산 / 총수익률 / 연환산 / 연도 MDD | §1.1 + §1.2 | `compute_kpi()` 시그니처 고정 |
| D-19 | Tab A universe = QQQ/SPY/KS200/SCHD/JEPI/WBI **6종** | §8.2 | API 입력 검증 |
| D-20 | Tab B 자산 = QQQ/SPY/KS200 **3종만** | §9.2 | strategy 라우터 입력 검증 |
| D-21 | Tab C preset = **4개 고정**, 사용자 비중 편집 불가 | §10.5 | portfolio 라우터 입력 검증 |

`compute_kpi` 등 핵심 함수에 결정 ID 주석을 남긴다:

```python
def step(self, date, price_today, prices_local):
    if date < self.grace_end:        # D-9: 12개월 grace
        return None
    ...
    if (price_today / prices_local.shift(60)[date]) >= 1.20:   # D-10
        ...
    self.lock_until_year = date.year   # D-8
```

---

## 모듈 구조

`backend/research_engine/simulation/` (Phase 2 신규):

```
simulation/
├── __init__.py
├── replay.py            # 적립식 replay (Tab A 기본)
├── strategy_a.py        # 고가매도-저가재매수 (Tab B 첫 옵션)
├── strategy_b.py        # 70% 정기 + 30% 대기 (Tab B 두 번째 옵션)
├── portfolio.py         # 고정 포트폴리오 + 연 1회 리밸런싱 (Tab C)
├── padding.py           # cyclic returns padding (D-2)
├── wbi.py               # WBI synthetic 생성 (D-5)
├── fx.py                # USD↔KRW 환산
└── mdd.py               # 캘린더 연도 MDD (D-11)
```

라우터:
- `backend/api/routers/simulation.py` — `POST /v1/silver/simulate/{replay,strategy,portfolio}`
- `backend/api/routers/fx.py` — `GET /v1/fx/usd-krw`

Agentic tool (Phase 4 등록):
- `simulation_replay`, `simulation_strategy`, `simulation_portfolio` 신규
- `strategy_classify`, `strategy_report` 제거 (Bronze tool, StrategyPage drop으로 무효)

---

## 공통 입력 / KPI

```python
@dataclass
class SimInput:
    asset_codes: list[str]
    monthly_amount: int            # 30/50/100/200/300 만원
    period_years: int              # 3/5/10
    base_currency: Literal["KRW", "local"]   # 표시 통화

def compute_kpi(curve_krw, total_deposit_krw, period_years) -> dict:
    """D-18: KPI 4종 시그니처 고정."""
    final = curve_krw[-1]
    total_return = (final - total_deposit_krw) / total_deposit_krw
    annualized = (final / total_deposit_krw) ** (1 / period_years) - 1
    worst_mdd = min(mdd_by_calendar_year(curve_krw).values())   # D-11
    return {
        "final_asset_krw": final,
        "total_return": total_return,
        "annualized_return": annualized,
        "yearly_worst_mdd": worst_mdd,
    }
```

KPI 추가/제거 금지. 이름 바꾸지 말 것 (프론트 `KpiCard.tsx` + Agentic tool과 계약).

---

## 핵심 패턴

### 1. 적립식 replay (`replay.py`)

- 적립일: **자산별 매월 첫 거래일** (KRX vs NYSE 캘린더 다름)
- 적립 금액: KRW 고정 → USD 자산은 적립일 종가 환율로 KRW→USD fractional 매수
- 평가: 매 거래일 KRW 평가액 = USD 보유 × 그날 환율 + KRW 자산 평가액
- 배당(D-4): 매 거래일 보유분에 `(1 + annual_yield/252)` 적용

```python
def replay(asset_code, monthly_amount_krw, period_years, fx_daily, prices) -> EquityCurve:
    portfolio = {"shares": 0.0}
    curve = []
    for date in trading_days(asset_code, period_years):
        # D-17: 1) 정기 적립 먼저
        if is_first_trading_day_of_month(date, asset_code):
            krw = monthly_amount_krw
            if asset_currency(asset_code) == "USD":
                usd = krw / fx_daily[date]
                portfolio["shares"] += usd / prices[date]
            else:
                portfolio["shares"] += krw / prices[date]

        # D-4: 2) 배당 재투자 매일
        portfolio["shares"] *= (1 + annual_yield(asset_code) / 252)

        # 3) 평가
        local_value = portfolio["shares"] * prices[date]
        krw_value = local_value * (fx_daily[date] if asset_currency(asset_code) == "USD" else 1)
        curve.append((date, krw_value, local_value))
    return curve
```

### 2. 전략 A — 고가 매도 후 저가 재매수 (`strategy_a.py`)

**lock 사이클 (D-7~D-10)** — 가장 자주 깨지는 부분.

- 상태: `STATE_NEUTRAL` ↔ `STATE_SOLD`
- 매도 트리거: 60거래일 전 대비 ≥ 20% (D-10), 보유의 30% 매도
- 재매수 트리거: 20거래일 전 대비 ≤ −10% (§1.1) **또는** 매도일 + 365일 (D-7)
- 페어 완성 후 `lock_until_year = 매도일.year` 갱신 → 같은 해 매도 시그널 무시 (D-8)
- 적립 시작 후 첫 12개월은 매도 트리거 자체 무시 (D-9 grace)
- 트리거 판정은 **현지통화 가격** (D-6)

```python
class StrategyA:
    def __init__(self, asset_code, period_start):
        self.state = "NEUTRAL"
        self.lock_until_year = None
        self.sell_date = None
        self.cash_held = 0.0
        self.grace_end = period_start + relativedelta(months=12)   # D-9

    def step(self, date, price_today, prices_local):
        if date < self.grace_end:                                  # D-9
            return None

        if self.state == "NEUTRAL":
            if self.lock_until_year is None or date.year > self.lock_until_year:   # D-8
                ratio = price_today / prices_local.shift(60)[date]                  # D-10
                if ratio >= 1.20:
                    sell_qty = portfolio.shares * 0.30
                    self.cash_held = sell_qty * price_today
                    portfolio.shares -= sell_qty
                    self.state = "SOLD"
                    self.sell_date = date

        elif self.state == "SOLD":
            crash = price_today / prices_local.shift(20)[date] <= 0.90
            forced = date >= self.sell_date + timedelta(days=365)   # D-7
            if crash or forced:
                portfolio.shares += self.cash_held / price_today
                self.cash_held = 0
                self.state = "NEUTRAL"
                self.lock_until_year = date.year                    # D-8 갱신
```

> "매도일 + 365일"은 **달력 일수 365일**이지 거래일이나 "매도해의 12월 말"이 아니다. draft 원안과 다르다.

### 3. 전략 B — 70% 정기 + 30% 대기 (`strategy_b.py`)

```python
class StrategyB:
    def step_monthly_deposit(self, date, monthly_krw):
        self.buy_at_market(monthly_krw * 0.70, date)
        self.reserve_pool += monthly_krw * 0.30

    def step_daily(self, date, price_today, prices):
        if price_today / prices.shift(20)[date] <= 0.90:    # 급락 트리거
            self.buy_at_market(self.reserve_pool, date)
            self.reserve_pool = 0
        elif date == last_trading_day_of_year(date.year):   # 12월 강제 매수
            self.buy_at_market(self.reserve_pool, date)
            self.reserve_pool = 0
```

전략 B는 §1.1 원안 그대로. "12월 마지막 거래일"은 캘린더 연도 마지막 거래일이며, 매년 발생. 전략 A의 365일 룰과 혼동 금지.

### 4. 포트폴리오 적립 (`portfolio.py`)

- 4개 preset 고정(D-21), 사용자 비중 편집 불가
- 매월 적립금: 목표 비중대로 즉시 분배
- 연간 리밸런싱: 매년 마지막 거래일, 보유분 포함 실제 매도/매수
- 60/20/20 = 주식·ETF 60% + TLT 20% + BTC 20%
- 60% 슬롯 후보: QQQ / KOSPI200 / 삼성+하이닉스 50:50 / NVDA+GOOGL+TSLA 1:1:1
- 소수 단위 매수 허용 (§1.1 lock)
- WBI 미포함 (§10.6)

### 5. Padding (`padding.py`) — D-2

```python
def pad_returns(returns_actual: np.ndarray, target_days: int, start_price: float) -> tuple[np.ndarray, np.ndarray]:
    """D-2: cyclic 복제로 일별 수익률 패딩 + reverse-cumprod로 가격 산정."""
    needed = target_days - len(returns_actual)
    padding_returns = []
    while len(padding_returns) < needed:
        take = min(needed - len(padding_returns), len(returns_actual))
        padding_returns.extend(returns_actual[:take])

    # reverse-cumprod: actual 시작 가격에서 거꾸로 풀어 padding 가격 산정
    # → padding 끝나는 시점의 가격이 actual의 첫 가격과 정확히 이어짐 (점프 X)
    padding_prices = [start_price]
    for r in reversed(padding_returns):
        padding_prices.append(padding_prices[-1] / (1 + r))
    padding_prices = list(reversed(padding_prices[1:]))   # 시작점 제외

    returns_full = np.concatenate([padding_returns, returns_actual])
    prices_full = np.concatenate([padding_prices, np.cumprod(1 + returns_actual) * start_price])
    return returns_full, prices_full
```

검증: padding 평균 수익률이 actual 평균 ±0.1% 이내, padding 끝가격 == actual 시작가격 (정확히 일치).

자산별 적용:
- JEPI: 약 5년 padding 필요 (allow_padding=True)
- 나머지 12종: 10년 충족, padding 불필요

### 6. WBI (Warren Buffett Index) synthetic (`wbi.py`) — D-5

```python
import numpy as np

def generate_wbi(n_trading_days: int, initial_price: float = 100.0, seed: int = 42) -> np.ndarray:
    """D-5: 거래일 등비 + GBM 노이즈, 시드 42, KRW 자산."""
    annual_return = 0.20
    trading_days_per_year = 252
    mu = (1 + annual_return) ** (1 / trading_days_per_year) - 1   # ≈ 0.0727%/일
    sigma = 0.01                                                   # σ = 1%/일
    mu_adj = mu - 0.5 * sigma ** 2                                 # GBM drift 보정

    rng = np.random.default_rng(seed=seed)
    returns = rng.normal(loc=mu_adj, scale=sigma, size=n_trading_days)
    prices = np.cumprod(1 + returns) * initial_price
    return prices
```

**reproducibility 필수**: 시드 42로 재실행 시 동일 결과. CI에서 첫 100거래일 가격 hash로 회귀 검증 권장.

검증: 10년 평균 연환산 수익률 = 20% ±0.5%, σ = 1% ±0.05%.

### 7. fx (`fx.py`)

```python
def get_fx_rate(date: datetime.date, fx_daily: dict[date, Decimal]) -> Decimal:
    """KR 휴장일 등 결측 시 forward-fill (가장 최근 영업일 환율)."""
    while date not in fx_daily:
        date -= timedelta(days=1)
        if date < EARLIEST_DATE:
            raise FxLookupError(date)
    return fx_daily[date]
```

USD 자산 평가는 매 거래일 환율 사용 (§1.1 lock). 적립 시점 환율과 평가 시점 환율은 다를 수 있음 (환차익/손).

### 8. MDD (`mdd.py`) — D-11

```python
def mdd_by_calendar_year(equity_curve_krw) -> dict[int, float]:
    """D-11: 캘린더 연도(Jan-Dec)별 drawdown 중 최악."""
    by_year = {}
    for year, year_slice in groupby(equity_curve_krw, key=lambda r: r.date.year):
        prices = np.array([r.krw_value for r in year_slice])
        running_max = np.maximum.accumulate(prices)
        drawdown = (prices - running_max) / running_max   # 음수
        by_year[year] = float(drawdown.min())
    return by_year
```

표시: "연도 기준 최대 손실폭 −24% (2022년)". 회계연도/이동 12개월/peak-to-trough 누적이 아니다.

---

## 자주 빠지는 함정 (Anti-Patterns)

| 함정 | 증상 | 올바른 방식 |
|---|---|---|
| 전략 A 강제 재매수 = "매도해 12월 말" | draft §9.4 원안 추론 | **D-7**: `매도일 + 365일` (달력 일수) |
| `lock_until_year`를 매도 시점에 갱신 | 같은 해 한 번 더 매도 가능해짐 | **D-8**: **재매수 시점**에 `매도일.year`로 갱신 |
| grace period 누락 | 적립 시작 직후 매도 트리거 발생 | **D-9**: 적립 시작 후 12개월 trigger 무시 |
| 60거래일 ratio를 **KRW 가격**으로 계산 | 환율 변동이 ratio 왜곡 | **D-6**: USD 자산은 USD 가격으로 ratio |
| padding을 가격 직접 복제 | 가격 점프 발생 | **D-2**: 일별 수익률만 cyclic, reverse-cumprod로 가격 산정 |
| WBI 시드 미고정 / 매번 재계산 | reproducibility 깨짐 | **D-5**: `np.random.default_rng(seed=42)` |
| WBI를 USD로 처리 | 환율 영향 발생 | **D-5**: KRW 자산 (`asset_master.currency='KRW'`) |
| MDD를 peak-to-trough 누적으로 계산 | 캘린더 정의와 다름 | **D-11**: 매년 1/1 ~ 12/31 슬라이스 후 최악 |
| 적립과 트리거 같은 날 → 트리거 먼저 | 이벤트 순서 깨짐 | **D-17**: 적립 먼저, 그 다음 strategy.step() |
| 배당을 월별 / 연말 일시 적용 | 평가액 곡선 계단 모양 | **D-4**: 매 거래일 (1+yield/252) 균등 분할 |
| KPI 이름 변경 (`return_pct` 등) | 프론트/Agentic tool 계약 깨짐 | **D-18**: 4종 이름 고정 |
| Tab A에 NVDA/TSLA 등 8종 자산 노출 | universe 위반 | **D-19**: 6종(QQQ/SPY/KS200/SCHD/JEPI/WBI)만 |
| 백테스트(`backtest_run` 등) 패턴 재사용 | 의미·테이블 다름 | Bronze backtest는 Phase 4에서 drop, simulation은 별개 |

---

## 검증 전략

### Unit test (Phase 2)

- `padding.py`: 3년 → 10년 패딩 결과 길이/연속성/평균 수익률 보존 (±0.1% 오차)
- `wbi.py`: 시드 42 결과 reproducibility (동일 입력 → 동일 출력), 10년 평균 = 20% ±0.5%
- `strategy_a.py`: 매도 후 같은 해 매도 시그널이 무시되는지 (D-8), 365일 강제 재매수 (D-7), 12개월 grace (D-9)
- `mdd.py`: 캘린더 연도 분리, 연도 경계 across drawdown은 분리되어야 함
- `fx.py`: 결측일 forward-fill, EARLIEST_DATE 이전 조회 시 명시적 에러

### Integration test (Phase 2)

- Tab A: QQQ + SPY + KS200 10년 적립 → KPI 4개 산출, 차트 row 수 ≈ 2520 거래일
- Tab B: QQQ 적립식 vs 전략 A — lock 페어 사이클이 적어도 1회 발생
- Tab C: QQQ + TLT + BTC 60/20/20 — 매년 마지막 거래일에 리밸런싱 트랜잭션 발생

### Cross-check fixture

- **QQQ 10년 적립 known-good**: Portfoliovisualizer / backtest.curvo.eu 외부 도구 결과를 fixture로 저장
- silver-rev1 결과가 fixture와 ±2% 이내에서 일치하는지 CI에서 검증

---

## 사용자 흐름 (Tab A/B/C → API → simulation)

```
[Frontend]                          [Backend]
CompareMainPage
  ↓ 공통 입력 (period_years, monthly_amount)
TabA_SingleAsset    ─POST /v1/silver/simulate/replay──→     replay.py
TabB_AssetVsStrategy ─POST /v1/silver/simulate/strategy─→  strategy_a.py / strategy_b.py
TabC_AssetVsPortfolio ─POST /v1/silver/simulate/portfolio→ portfolio.py

EquityChart    ←── EquityCurve (date, krw_value, local_value)
KpiCard        ←── compute_kpi() 결과 4종 (D-18)
IndicatorCard  ←── 별도 /v1/signals (Bronze 유지)

ChatPage Agentic tool ──┬─ simulation_replay
                        ├─ simulation_strategy   → 같은 simulation 모듈 호출 (단일 source 보장)
                        └─ simulation_portfolio
```

> A-004 교훈 적용: 프론트 페이지와 Agentic tool이 **동일 simulation 함수**를 호출. 데이터 소스 불일치 방지.

---

## Related Docs

- `docs/silver-masterplan.md` — 단일 source of truth (특히 §2 자산표, §3 시뮬레이션 명세, §11 미해결 후속 과제)
- `docs/draft-rev1.md` — §1.1 lock 항목 인용 시
- `docs/silver-rev1-analysis.md` — Part B 7대 허들 (B-2 WBI / B-5 전략 / B-6 MDD)
- `dev/active/project-overall/project-overall-context.md` §3 — 본 skill의 D-1~D-21과 동일 표 (project 단위)
- `dev/active/silver-rev1-phase2/` — Phase 2 dev-docs (생성 예정)
- `.claude/skills/backend-dev/SKILL.md` — Router-Service-Repository 패턴 (라우터 작성 시)
- `project-wrapup/lessons-learned.json` — A-004 (대시보드 ↔ Agentic 데이터 소스 일치)

---

## Status

- **Active during**: Silver gen Phase 2 (구현) ~ Phase 5 (안정화)
- **Sunset**: Silver gen 종료 후 gold gen에서 시뮬레이션 명세 변경 시 업데이트 또는 archive
