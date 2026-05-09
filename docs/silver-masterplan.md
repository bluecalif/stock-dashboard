# Stock Dashboard Silver rev1 — Masterplan

> Generated: 2026-05-09
> Source: `docs/draft-rev1.md` (Silver gen 명세 초안 §1.1 세션 고정 결정사항) + `docs/silver-rev1-analysis.md` (Part B 허들 / Part C Gap Map / Part D 인터뷰 답변)
> 산출 단계: 본 문서로 기획·분석 종료. 코딩은 §8 Phase 분할에 따라 후속 세션에서 진행.

---

## 0. 인터뷰 답변 요약 (역추적용)

| Q# | 항목 | 답변 |
|---|---|---|
| Q1-1 | JEPY ticker | name·ticker 모두 **JEPI** (JPMorgan, 2020년 출시, ~5년 history) |
| Q1-2 | history 부족 시 padding | **일별 수익률(returns) cyclic 복제** — 가격 점프 없음, 추세·변동성 보존 |
| Q1-3 | USD/KRW 데이터 | **FDR `USD/KRW` 10년 backfill, `fx_daily` 신규 테이블** |
| Q1-4 | 배당/이자 처리 | **공시 배당률 균등 분할** (예: SCHD 연 3.5% → 매월 0.292%) |
| Q2-5 | WBI 일별 수익률 | **거래일 등비 + GBM 노이즈** (μ=`(1.20)^(1/252)-1`, σ=1%/일, drift 보정 `μ-σ²/2`) |
| Q2-6 | WBI 통화 | **KRW 자산** (환율 영향 없음) |
| Q3-9 | 트리거 통화 | **현지통화 가격 기준** (USD 자산은 USD 가격으로 ±20% 판정) |
| Q4-10 | 급등 조건 정의 | **`오늘종가 / 60거래일 전 종가 ≥ 1.20`** |
| Q4-11~13 | 페어·강제 재매수·lock | **강제 재매수 = 매도일 + 365일**, lock = 매도해 ~ 재매수해 (포함) |
| Q4-14 | grace period | **12개월** (적립식 시작 후 첫 12개월 매도 트리거 무시) |
| Q5-15 | MDD 연도 단위 | **캘린더 연도** |
| Q6-16 | nav 위치 | **상단 가로 nav** |
| Q6-18 | Tab A 자산 추가 UI | **`+` 버튼 + 자산 picker drawer** |
| Q6-19 | chat/AI | **그대로 유지** (Bronze Phase F Agentic AI 유지) |
| Q6-20 | 모바일 | **rev1 필수** (반응형) |
| Q7-21 | 지표 카드 내용 | **개별 RSI/MACD/ATR 값 + 상태 라벨** |
| Q7-23 | 신호 상세 페이지 | **단순 단순화** (기존 IndicatorSignalPage 항목만 줄임) |
| Q8-24 | Bronze→Silver 전환 | **빅뱅 교체** (사용자 1명 → 다운타임 0) |
| Q8-26 | StrategyPage drop 백엔드 | **DB 테이블도 drop** (backtest_run / equity_curve / trade_log) |

§1.1 lock 항목 (인터뷰 제외): 탭 A 기본 3 자산, 공통 입력(기간/적립금/자산), 기간 프리셋, 적립금 프리셋, 전략 A 급락 조건, 이벤트 순서, Tab C 리밸런싱 방식, 환율 매 날짜 사용, 신호 최소 범위, 출시 기준(전체 자산군 지원), KPI 4종, 레거시 처리.

---

## 1. 제품 정의 & 성공 기준

### 1.1 제품 정의

Silver rev1은 **초보 투자자용 적립식 비교 도구**다. Bronze의 폴리시가 아니라 **다른 제품**이며, IA 재편을 동반한 빅뱅 전환으로 cut-over한다.

- 메인 진입: `적립식 비교` 단일 메뉴
- 메인 구조: 3탭 (단일자산 / 자산vs전략 / 자산vs포트폴리오)
- 보조: 신호 상세 (단순화)
- chat/AI: Bronze Phase F Agentic AI 유지

### 1.2 KPI (§1.1 lock)

| 순위 | 지표 | 정의 |
|---|---|---|
| 1 | 최종 자산 | 시뮬레이션 종료 시점 KRW 평가금액 |
| 2 | 총 수익률 | (최종 자산 − 총 적립원금) / 총 적립원금 |
| 3 | 연환산 수익률 | (최종/원금)^(1/연수) − 1 |
| 4 | 연도 기준 최대 손실폭 | 캘린더 연도별 적립식 누적 자산가치 곡선의 (고점 → 저점) drawdown 중 최악 |

### 1.3 성공 기준

- 첫 진입 후 "무엇을 비교하는 화면인지" 즉시 보임
- Tab A/B/C 모두 동작, 자산/전략/preset 제한이 UI와 계산에서 일치
- WBI가 실자산처럼 수집 로직을 타지 않음
- Bronze 라우트(`/`, `/prices`, `/correlation`, `/strategy`) 차단/redirect 일관 적용

---

## 2. 자산/데이터 확정표

### 2.1 rev1 자산 universe (총 13종 + WBI synthetic)

| 표시명 | ticker | 카테고리 | 통화 | 데이터 출처 | history 충족 |
|---|---|---|---|---|---|
| QQQ | QQQ | US ETF | USD | FDR | ✅ 10년+ |
| SPY | SPY | US ETF | USD | FDR | ✅ 10년+ |
| KOSPI200 | KS200 | KR 지수 | KRW | FDR (기존) | ✅ |
| SCHD | SCHD | US ETF | USD | FDR | ✅ (2011 출시) |
| **JEPI** | JEPI | US ETF | USD | FDR | ⚠️ 5년 (cyclic padding) |
| TLT | TLT | US ETF | USD | FDR | ✅ (2002 출시) |
| 비트코인 | BTC | Crypto | KRW | FDR (기존, BTC/KRW) | ✅ |
| 엔비디아 | NVDA | US Stock | USD | FDR | ✅ 10년+ |
| 구글 | GOOGL | US Stock | USD | FDR | ✅ 10년+ |
| 테슬라 | TSLA | US Stock | USD | FDR | ✅ (2010 출시) |
| 삼성전자 | 005930 | KR Stock | KRW | FDR (기존) | ✅ |
| 하이닉스 | 000660 | KR Stock | KRW | FDR (기존) | ✅ |
| WBI | (synthetic) | Benchmark | KRW | 계산식 | n/a |

**참고**: draft-rev1.md §7.1의 `JEPY` 표기는 본 문서에서 `JEPI`로 통일.

### 2.2 기존 자산 처리 (draft §7.3)

`SOXL`, `GC=F`(금), `SI=F`(은)는 삭제하지 않고 backend에 유지. Silver 메인 비교 대상에는 미포함. 신호 자산에도 미포함.

### 2.3 USD/KRW 환율 (Q1-3)

- 출처: FDR `USD/KRW` 일봉
- 신규 테이블 `fx_daily` (10년 backfill)
- 컬럼: `date PK`, `usd_krw_close DECIMAL(10,4)`
- 갱신: 일 1회 (Bronze collector schedule에 fold)

### 2.4 배당/이자 처리 (Q1-4) — 공시 배당률 균등 분할

asset_master에 `annual_yield NUMERIC(6,4)` 컬럼 추가. 매 거래일 종가에 일별 배당 적용:

```python
daily_dividend_rate = annual_yield / 252  # 거래일 기준
# 적립금에 추가되는 가상 현금 흐름으로 처리하지 않고,
# 보유 평가액에 매일 (1 + daily_dividend_rate)배 적용
```

자산별 배당률 fixture (rev1 시작 시점):

| 자산 | 연 배당률 |
|---|---|
| SCHD | 3.5% |
| JEPI | 8.0% |
| TLT | 3.8% |
| SPY | 1.3% |
| QQQ | 0.6% |
| KS200 (배당 ETF 대체값) | 1.5% |
| 005930 | 2.5% |
| 000660 | 1.0% |
| NVDA / GOOGL / TSLA | 0.0% |
| BTC / WBI | 0.0% |

> rev1 운영 중 실제 배당락 데이터로 교체할지는 후속 과제. 현재는 단순화 우선.

### 2.5 WBI synthetic 정의 (Q2-5, Q2-6)

- 통화: **KRW** (환율 영향 없음)
- 일별 수익률 시뮬레이션:

```python
import numpy as np

annual_return = 0.20
trading_days = 252
mu = (1 + annual_return) ** (1 / trading_days) - 1   # ≈ 0.0727%/일
sigma = 0.01                                          # σ = 1%/일

# GBM drift 보정으로 평균 정확히 연 20% 보존
mu_adj = mu - 0.5 * sigma ** 2

rng = np.random.default_rng(seed=42)   # 결정적 reproducibility
n = number_of_trading_days
returns = rng.normal(loc=mu_adj, scale=sigma, size=n)

prices = np.cumprod(1 + returns) * INITIAL_PRICE   # INITIAL_PRICE는 임의 (예: 100)
```

- 시드 고정으로 재실행 시 동일 결과
- 차트에 다른 자산과 함께 그려도 매끈한 직선이 아님 (체감 사기 느낌 ↓)

### 2.6 history 부족 자산 padding (Q1-2)

10년 시뮬레이션을 요구하는데 자산 history가 N년(N<10)이면:

```python
# 보유: returns_actual = [r1, r2, ..., rN]   (실제 일별 수익률)
# 필요: 총 (10*252) 일

needed = TARGET_DAYS - len(returns_actual)
padding = []
while len(padding) < needed:
    take = min(needed - len(padding), len(returns_actual))
    padding.extend(returns_actual[:take])

# padding을 actual 앞에 prepend
returns_full = padding + returns_actual.tolist()

# 시작가는 actual의 첫 날 가격을 padding 종료 시점으로 거꾸로 풀어 산정
# 즉 prices = first_actual_price를 기준으로 reverse-cumprod로 padding 가격 계산
```

알고리즘 핵심:
- **수익률 시퀀스만 cyclic 복제** → 가격 점프 없음
- padding 구간은 actual 시작 가격에서 reverse-cumprod로 거슬러 올라가 산정
- 변동성·추세 패턴 보존
- 차트에 padding 구간 표시 (옅은 회색 영역 + "padding 구간" 라벨)

자산별 적용 여부:
- JEPI: 약 5년 padding 필요 → padding 구간 명시
- 나머지: 10년 충족, padding 불필요

### 2.7 asset_master 스키마 변경

```sql
ALTER TABLE asset_master ADD COLUMN currency VARCHAR(8) NOT NULL DEFAULT 'KRW';
ALTER TABLE asset_master ADD COLUMN annual_yield NUMERIC(6,4) NOT NULL DEFAULT 0;
ALTER TABLE asset_master ADD COLUMN history_start_date DATE;        -- 데이터 시작일
ALTER TABLE asset_master ADD COLUMN allow_padding BOOLEAN DEFAULT FALSE;
ALTER TABLE asset_master ADD COLUMN display_name VARCHAR(64);       -- "엔비디아" 등 한국어 표시
```

---

## 3. 시뮬레이션 엔진 명세

### 3.1 모듈 위치

`backend/research_engine/simulation/` (신규)

```
simulation/
├── __init__.py
├── replay.py            # 적립식 replay (Tab A 기본)
├── strategy_a.py        # 고가매도-저가재매수 (Tab B)
├── strategy_b.py        # 70% 정기 + 30% 대기 (Tab B)
├── portfolio.py         # 고정 포트폴리오 + 연 1회 리밸런싱 (Tab C)
├── padding.py           # cyclic returns padding (Q1-2)
├── wbi.py              # WBI synthetic 생성 (Q2)
├── fx.py               # USD↔KRW 환산
└── mdd.py              # 캘린더 연도 MDD (Q5)
```

### 3.2 공통 입력

```python
@dataclass
class SimInput:
    asset_codes: list[str]         # 비교 대상
    monthly_amount: int            # 30/50/100/200/300 만원
    period_years: int              # 3/5/10
    base_currency: Literal["KRW", "local"]   # 표시 통화
```

### 3.3 적립식 replay (Tab A)

- 적립일: 매월 첫 거래일 (자산별 캘린더)
- 적립 금액: KRW 고정
- USD 자산: 적립일 종가 환율로 KRW→USD 환산 후 fractional 매수
- 평가: 매 거래일 KRW 평가액 = USD 보유 × 그날 환율 + KRW 자산 평가액
- 배당: 매 거래일 보유 평가액에 `(1 + annual_yield/252)` 적용 (재투자 가정)

```python
def replay(asset_code, monthly_amount_krw, period_years, fx_daily, prices) -> EquityCurve:
    portfolio = {"cash": 0, "shares": 0.0}
    curve = []
    for date in trading_days(period_years):
        # 1. 매월 첫 거래일이면 적립
        if is_first_trading_day_of_month(date, asset_code):
            krw = monthly_amount_krw
            if asset_currency == "USD":
                usd = krw / fx_daily[date]
                portfolio["shares"] += usd / prices[date]   # fractional
            else:
                portfolio["shares"] += krw / prices[date]

        # 2. 배당 재투자 (매일 보유분에 적용)
        portfolio["shares"] *= (1 + annual_yield[asset_code] / 252)

        # 3. 평가
        local_value = portfolio["shares"] * prices[date]
        krw_value = local_value * (fx_daily[date] if asset_currency == "USD" else 1)
        curve.append((date, krw_value, local_value))
    return curve
```

### 3.4 전략 A — 고가 매도 후 저가 재매수 (Q4-10~14)

```python
STATE_NEUTRAL = "NEUTRAL"
STATE_SOLD = "SOLD"

class StrategyA:
    def __init__(self, asset_code, period_start):
        self.state = STATE_NEUTRAL
        self.lock_until_year = None
        self.sell_date = None
        self.cash_held = 0.0      # 매도 자금
        self.grace_end = period_start + relativedelta(months=12)   # Q4-14

    def step(self, date, price_today, prices_local_currency):
        # Q4-14: 첫 12개월 grace period
        if date < self.grace_end:
            return None

        if self.state == STATE_NEUTRAL:
            # Q4-10: 60거래일 lookback ratio
            if (lock_until_year is None or date.year > self.lock_until_year):
                price_60d_ago = prices_local_currency.shift(60)[date]
                if price_today / price_60d_ago >= 1.20:
                    sell_amount = portfolio.shares * 0.30
                    self.cash_held = sell_amount * price_today
                    portfolio.shares *= 0.70
                    self.state = STATE_SOLD
                    self.sell_date = date

        elif self.state == STATE_SOLD:
            # 급락 트리거: 20거래일 전 대비 10% 하락 (§1.1 lock)
            price_20d_ago = prices_local_currency.shift(20)[date]
            crash = price_today / price_20d_ago <= 0.90
            forced = date >= self.sell_date + timedelta(days=365)

            if crash or forced:
                portfolio.shares += self.cash_held / price_today
                self.cash_held = 0
                self.state = STATE_NEUTRAL
                self.lock_until_year = date.year   # 매도해~재매수해 lock
```

> §1.1 이벤트 순서 lock: "정기 적립 후 조건 실행" — 같은 날 적립과 트리거 겹치면 적립 먼저.
> Q3-9: 트리거 판정은 **현지통화 가격 기준** (USD 자산은 USD 가격으로 60거래일 ratio 계산).

### 3.5 전략 B — 70% 정기 + 30% 대기 (draft §9.5)

```python
class StrategyB:
    def step_monthly_deposit(self, date, monthly_krw):
        regular = monthly_krw * 0.70
        reserved = monthly_krw * 0.30
        self.buy_at_market(regular, date)
        self.reserve_pool += reserved

    def step_daily(self, date, price_today, prices):
        price_20d_ago = prices.shift(20)[date]
        if price_today / price_20d_ago <= 0.90:
            # 대기 자금 전액 매수
            self.buy_at_market(self.reserve_pool, date)
            self.reserve_pool = 0
        elif date == last_trading_day_of_year(date.year):
            # 12월 마지막 거래일 강제 매수
            self.buy_at_market(self.reserve_pool, date)
            self.reserve_pool = 0
```

> 전략 B는 §1.1 원안 그대로 유지 (수정 없음). "12월 마지막 거래일"은 캘린더 연도 마지막 거래일.

### 3.6 포트폴리오 적립식 (Tab C, draft §10)

- 기본 비중: 주식/ETF 60% + TLT 20% + BTC 20%
- 매월 적립금: 목표 비중대로 즉시 분배
- 연간 리밸런싱: 매년 마지막 거래일, 보유분 포함 실제 매도/매수
- 60% 슬롯 후보:
  - QQQ
  - KOSPI200
  - 삼성전자/하이닉스 1:1 (50% / 50%)
  - 엔비디아/구글/테슬라 1:1:1
- 소수 단위 매수 허용 (§1.1 lock)
- WBI 미포함 (draft §10.6)

### 3.7 MDD 계산 (Q5-15: 캘린더 연도)

```python
def mdd_by_calendar_year(equity_curve_krw) -> dict[int, float]:
    """연도별 MDD 중 최악을 반환."""
    by_year = {}
    for year, year_slice in groupby(equity_curve_krw, key=lambda r: r.date.year):
        prices = [r.krw_value for r in year_slice]
        running_max = np.maximum.accumulate(prices)
        drawdown = (prices - running_max) / running_max     # 음수
        by_year[year] = drawdown.min()
    return by_year

worst_year_mdd = min(mdd_by_calendar_year(curve).values())
```

표시: "연도 기준 최대 손실폭 −24% (2022년)". draft §11 표현 규칙 준수.

### 3.8 KPI 산출

```python
def compute_kpi(curve_krw, total_deposit_krw, period_years):
    final = curve_krw[-1]
    total_return = (final - total_deposit_krw) / total_deposit_krw
    annualized = (final / total_deposit_krw) ** (1 / period_years) - 1
    worst_mdd = min(mdd_by_calendar_year(curve_krw).values())
    return {
        "final_asset_krw": final,
        "total_return": total_return,
        "annualized_return": annualized,
        "yearly_worst_mdd": worst_mdd,
    }
```

---

## 4. IA & 화면 명세

### 4.1 라우트 (Q6-16: 상단 가로 nav)

```
/                       → /silver/compare (redirect)
/silver/compare         → 적립식 비교 메인 (Tab A/B/C)
/silver/signals         → 신호 상세 (단순화된 IndicatorSignalPage 후신)
/silver/chat            → Agentic chat (Bronze Phase F 유지, Q6-19)
/silver/login           → 인증
/silver/profile         → 사용자 프로필

/prices, /correlation, /strategy, /indicators, /dashboard
                        → 모두 /silver/compare 로 redirect (Q8-25 자연 결정)
```

### 4.2 메인 헤더 (상단 가로 nav)

```
┌─────────────────────────────────────────────────────────────┐
│ Stock Dashboard   [적립식 비교] [신호] [Chat]  [👤 profile] │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 적립식 비교 메인 (`/silver/compare`)

```
┌─ 공통 입력 패널 ──────────────────────────────────────┐
│ 기간 [3년 | 5년 | ●10년]   월 적립금 [30 50 ●100 200 300]만원 │
└───────────────────────────────────────────────────────┘
┌─ 탭 ──────────────────────────────────────────────────┐
│ [● 단일자산] [ 자산vs전략 ] [ 자산vs포트폴리오 ]       │
└───────────────────────────────────────────────────────┘
┌─ Tab A 본문 ──────────────────────────────────────────┐
│ 비교 자산: [QQQ ✕] [SPY ✕] [KOSPI200 ✕] [+ 추가]      │
│ ┌─ 핵심 비교 차트 (누적 자산가치 KRW) ────────────────┐│
│ │  ╱──────QQQ                                         ││
│ │ ╱───────SPY                                         ││
│ │╱────────KS200                                       ││
│ └────────────────────────────────────────────────────┘│
│ ┌─ KPI 카드 (자산별 가로 스크롤) ────────────────────┐│
│ │ QQQ: 최종 X / 총수익 +Y% / 연환산 +Z% / MDD −W%    ││
│ └────────────────────────────────────────────────────┘│
│ ┌─ 해석 카드 (초보자용 문구) ────────────────────────┐│
│ │ "10년 적립으로 원금 1.2억이 X억으로 늘었습니다..." ││
│ └────────────────────────────────────────────────────┘│
│ ┌─ 위험 설명 카드 ────────────────────────────────────┐│
│ │ "최악의 한 해(2022)에 평가액이 24% 줄었습니다..."  ││
│ └────────────────────────────────────────────────────┘│
│ ┌─ 지표 요약 카드 (Q7-21) ───────────────────────────┐│
│ │ 자산  │ RSI(상태)  │ MACD(상태)   │ ATR(상태)      ││
│ │ QQQ   │ 62 (중립)  │ 골든크로스   │ 보통           ││
│ └────────────────────────────────────────────────────┘│
└───────────────────────────────────────────────────────┘
```

### 4.4 자산 추가 UI (Q6-18)

`+ 추가` 버튼 클릭 시 우측에서 drawer 슬라이드:

```
┌─ Drawer ──────────────┐
│ 자산 추가              │
│ ┌─ 카테고리 ──────────┐│
│ │ ☐ SCHD              ││
│ │ ☐ JEPI              ││
│ │ ☐ WBI (benchmark)   ││
│ └────────────────────┘│
│ [추가] [취소]          │
└────────────────────────┘
```

Tab A universe = §8.2 lock = QQQ/SPY/KS200/SCHD/JEPI/WBI 6종.

### 4.5 Tab B/C

draft §9, §10 그대로. UI 레이아웃은 Tab A와 동일 패턴 (입력 → 차트 → KPI → 해석 → 위험 → 지표).

Tab B 자산: QQQ/SPY/KS200 3종만 (§9.2 lock).
Tab C preset: 4개 (§10.5 lock). 사용자 비중 편집 불가.

### 4.6 신호 상세 페이지 (`/silver/signals`, Q7-23: 단순 단순화)

기존 `IndicatorSignalPage` 유지, 다음 항목만 노출:

- 자산 선택: QQQ/SPY/KS200/NVDA/GOOGL/TSLA/SEC/SKH (§12.3 lock 8종)
- 지표: RSI / MACD / ATR
- 차트: 가격 + RSI/MACD/ATR overlay
- 설명형 상태 라벨 (매수/매도 추천형 X)

draft §12 그대로.

### 4.7 모바일 (Q6-20: rev1 필수)

- 768px 미만: 탭 nav를 가로 스크롤로
- 차트는 세로 스택
- KPI 카드는 1열
- 자산 추가 drawer는 풀스크린 모달

---

## 5. 백엔드 변경 명세

### 5.1 신규 마이그레이션

```
alembic revision -m "silver_rev1_schema_changes"
```

```sql
-- 1. asset_master 컬럼 추가
ALTER TABLE asset_master ADD COLUMN currency VARCHAR(8) NOT NULL DEFAULT 'KRW';
ALTER TABLE asset_master ADD COLUMN annual_yield NUMERIC(6,4) NOT NULL DEFAULT 0;
ALTER TABLE asset_master ADD COLUMN history_start_date DATE;
ALTER TABLE asset_master ADD COLUMN allow_padding BOOLEAN DEFAULT FALSE;
ALTER TABLE asset_master ADD COLUMN display_name VARCHAR(64);

-- 2. fx_daily 테이블 신규 (Q1-3)
CREATE TABLE fx_daily (
    date DATE PRIMARY KEY,
    usd_krw_close NUMERIC(10,4) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. StrategyPage 관련 테이블 drop (Q8-26)
DROP TABLE backtest_trade_log;
DROP TABLE backtest_equity_curve;
DROP TABLE backtest_run;

-- 4. (선택) 시뮬레이션 결과 캐시 테이블
-- 본격 도입은 후속 과제. rev1은 매 요청 시 재계산.
```

### 5.2 collector 확장 (Q1-1, Q1-3)

`backend/collector/fdr_client.py:14`의 `SYMBOL_MAP` 확장:

```python
SYMBOL_MAP = {
    # 기존
    "KS200": "KS200",
    "005930": "005930",
    "000660": "000660",
    "SOXL": "SOXL",
    "BTC": "BTC/KRW",
    "GC=F": "GC=F",
    "SI=F": "SI=F",
    # 신규 8종
    "QQQ": "QQQ",
    "SPY": "SPY",
    "SCHD": "SCHD",
    "JEPI": "JEPI",       # JEPY 표기 → JEPI 통일
    "TLT": "TLT",
    "NVDA": "NVDA",
    "GOOGL": "GOOGL",
    "TSLA": "TSLA",
}
```

신규 collector 함수:

```python
# backend/collector/fx_collector.py
def collect_usd_krw(start_date, end_date) -> list[FxDaily]:
    df = fdr.DataReader("USD/KRW", start=start_date, end=end_date)
    return [FxDaily(date=d, usd_krw_close=Decimal(c)) for d, c in zip(df.index, df["Close"])]
```

### 5.3 API 라우터 변경

**제거**:
- `routers/backtests.py` (StrategyPage 관련)

**유지**:
- `routers/assets.py`, `prices.py`, `factors.py`, `signals.py`, `health.py`, `dashboard.py`, `correlation.py`, `chat.py`, `profile.py`, `analysis.py`, `auth.py`

**신규**:
- `routers/simulation.py` — 적립식 시뮬레이션
  - `POST /v1/silver/simulate/replay` — Tab A
  - `POST /v1/silver/simulate/strategy` — Tab B (전략 A/B)
  - `POST /v1/silver/simulate/portfolio` — Tab C
- `routers/fx.py` — 환율 조회 (`GET /v1/fx/usd-krw`)

### 5.4 Agentic AI (Phase F) 정리 (Q6-19, Q8-26)

- **유지**: chat 페이지, LangGraph state machine, classifier
- **tool 정리**:
  - 제거: `strategy_classify`, `strategy_report` (StrategyPage drop으로 무효)
  - 유지: `dashboard_summary`, `price_lookup`, `correlation_matrix`
  - 신규: `simulation_replay`, `simulation_strategy`, `simulation_portfolio` (Silver Tab A/B/C 호출)
- **A-004 교훈 적용**: 대시보드와 Agentic이 같은 simulation API를 호출하도록 일치

---

## 6. 프론트엔드 변경 명세

### 6.1 라우트 재편

```typescript
// frontend/src/App.tsx (rev1)
const router = createBrowserRouter([
  { path: "/", element: <Navigate to="/silver/compare" /> },
  { path: "/silver/compare", element: <CompareMainPage /> },   // 신규
  { path: "/silver/signals", element: <SignalDetailPage /> },  // IndicatorSignalPage 단순화
  { path: "/silver/chat", element: <ChatPage /> },             // Bronze 유지
  { path: "/silver/login", element: <LoginPage /> },
  { path: "/silver/profile", element: <ProfilePage /> },

  // Bronze 라우트 → Silver redirect
  { path: "/prices", element: <Navigate to="/silver/compare" /> },
  { path: "/correlation", element: <Navigate to="/silver/compare" /> },
  { path: "/dashboard", element: <Navigate to="/silver/compare" /> },
  { path: "/strategy", element: <Navigate to="/silver/compare" /> },
  { path: "/indicators", element: <Navigate to="/silver/compare" /> },
]);
```

### 6.2 신규 컴포넌트

```
frontend/src/pages/silver/
├── CompareMainPage.tsx           # /silver/compare
├── components/
│   ├── CommonInputPanel.tsx       # 기간/적립금
│   ├── TabNav.tsx                  # 단일자산/자산vs전략/자산vs포트폴리오
│   ├── TabA_SingleAsset.tsx        # 단일자산 비교
│   ├── TabB_AssetVsStrategy.tsx    # 자산 vs 전략 A/B
│   ├── TabC_AssetVsPortfolio.tsx   # 자산 vs 포트폴리오
│   ├── AssetPickerDrawer.tsx       # + 버튼 drawer (Q6-18)
│   ├── EquityChart.tsx             # 누적 자산가치 비교 차트
│   ├── KpiCard.tsx                 # 4개 KPI
│   ├── InterpretCard.tsx           # 초보자 해석 문구
│   ├── RiskCard.tsx                # 위험 설명
│   └── IndicatorCard.tsx           # RSI/MACD/ATR (Q7-21)
└── SignalDetailPage.tsx            # /silver/signals
```

### 6.3 폐기 컴포넌트

```
frontend/src/pages/StrategyPage.tsx       # drop (Q8-26)
frontend/src/pages/DashboardPage.tsx      # drop or redirect
frontend/src/pages/PricePage.tsx          # drop (PriceComparisonChart 로직만 EquityChart에 흡수)
frontend/src/pages/CorrelationPage.tsx    # drop
frontend/src/pages/IndicatorSignalPage.tsx # SignalDetailPage로 이전
```

### 6.4 재사용 (draft §14.3)

- `PricePage`의 정규화 수익률 비교 로직 → `EquityChart`로 흡수
- `IndicatorSignalPage`의 RSI/MACD/ATR 계산 → `IndicatorCard` + `SignalDetailPage`
- `StrategyPage`의 백테스트 코드는 직접 계승 안 함 (개념 다름)

### 6.5 Recharts 차트 사양

- **EquityChart**: `LineChart`, x=date, y=KRW 평가액, multi-series (자산별 색)
- **KpiCard**: 단순 numeric 노출
- **IndicatorCard**: 작은 sparkline + 현재값 + 라벨
- 다크 톤 시각 시스템 (draft §6.1, `docs/UX-design-ref.JPG` 참조)

---

## 7. 데이터 backfill 플랜

### 7.1 backfill 우선순위 (§1.1 lock: 출시 기준 = 전체 자산군 지원 완료)

```
1. 신규 8종 자산 일봉 10년 (QQQ/SPY/SCHD/JEPI/TLT/NVDA/GOOGL/TSLA)
2. USD/KRW 환율 일봉 10년 (fx_daily)
3. asset_master 컬럼 채움 (currency, annual_yield, history_start_date, allow_padding, display_name)
4. JEPI 약 5년 데이터 → padding 알고리즘 검증
5. WBI synthetic 시계열 생성 (시드 42, 10년)
```

### 7.2 backfill 검증

- 각 자산 일봉 row 수 확인 (10년 ≈ 2520 거래일)
- USD/KRW 결측일 확인 (KR 휴장일 처리)
- 자산별 calendar 정렬 (KRX vs NYSE) — Tab A 비교 시 forward-fill 사용
- 적립식 1차 known-good fixture: **QQQ 10년 적립 결과**를 외부 사이트(Portfoliovisualizer 등) 결과와 cross-check

### 7.3 Bronze 운영 영향

- backfill은 staging 환경에서 진행 → prod cut-over 시 한 번에 import
- Bronze 운영 중에는 fx_daily, asset_master 컬럼만 미리 추가 (backward-compatible)
- 신규 자산 일봉 테이블은 Bronze에 영향 없음

---

## 8. Phase 분할 (Bronze 운영 영향 최소화 순서)

### Phase 1 — 데이터 인프라 (Bronze 영향 0)

- asset_master 컬럼 추가 (DEFAULT 값으로 backward-compatible)
- fx_daily 테이블 신규
- collector SYMBOL_MAP 확장 (8종)
- USD/KRW collector 추가
- 신규 자산 backfill (staging)

검증: 데이터 row 수, padding 알고리즘 unit test, fixture cross-check.

### Phase 2 — 시뮬레이션 엔진 (Bronze 영향 0)

- `backend/research_engine/simulation/` 모듈 신규 작성
- replay / strategy_a / strategy_b / portfolio / padding / wbi / fx / mdd
- API 라우터 `/v1/silver/simulate/*` 추가
- Bronze 라우트는 그대로 운영

검증: KPI cross-check (외부 사이트 비교), edge case (history padding, grace period, lock 사이클).

### Phase 3 — 프론트엔드 신규 페이지 (Bronze 라우트와 병행 운영)

- `/silver/compare` 페이지 작성
- `/silver/signals` 작성 (IndicatorSignalPage 단순화)
- 컴포넌트 작성 (CompareMainPage, TabA/B/C, KpiCard, ...)
- 모바일 반응형 (Q6-20)

검증: UI 흐름, 모바일 768px breakpoint, 자산 추가 drawer 동작.

### Phase 4 — 빅뱅 cut-over (Q8-24)

- 1회 다운타임 시점 결정
- 모든 Bronze 라우트 → `/silver/compare` redirect 적용
- StrategyPage 코드 삭제, backtest 테이블 drop
- Agentic tool registration 정리 (strategy_classify/report 제거, simulation_* 추가)
- DashboardPage/PricePage/CorrelationPage 코드 삭제
- monitoring 1주

검증: 라우트 redirect 일관, Agentic AI tool 호출 정상, KPI 정합.

### Phase 5 — 후속 안정화

- 적립식 결과 LLM 해설 카드 (선택)
- 실제 배당락 데이터로 교체 (Q1-4 후속 과제)
- 시뮬레이션 결과 캐시 테이블 (성능 우려 시)

---

## 9. 테스트/검증 전략

### 9.1 Unit test

- `padding.py`: 3년 → 10년 패딩 결과 길이/연속성/평균 수익률 보존 (±0.1% 오차)
- `wbi.py`: 시드 42 결과 reproducibility, 평균 수익률 정확히 연 20% (10년 평균 ±0.5%)
- `strategy_a.py`: lock 사이클 (매도해 ~ 재매수해 매도 무시), 강제 재매수 365일, grace period 12개월
- `mdd.py`: 캘린더 연도 분리, drawdown 계산
- `fx.py`: 결측일 forward-fill

### 9.2 Integration test

- Tab A: QQQ + SPY + KS200 10년 적립 → KPI 4개 산출, 차트 데이터 row 수 검증
- Tab B: QQQ 적립식 vs 전략 A — 페어 사이클 발생 검증
- Tab C: QQQ + TLT + BTC 60/20/20 — 연 1회 리밸런싱 동작

### 9.3 Cross-check fixture

- **QQQ 10년 적립 known-good 결과**: Portfoliovisualizer 또는 backtest.curvo.eu 등 외부 도구 결과를 fixture로 저장
- rev1 결과가 fixture와 ±2% 안에서 일치하는지 CI에서 검증

### 9.4 사용자 검증 (사용자 1명 = 본인)

- Tab A/B/C 흐름 직접 확인
- 모바일 반응형 확인
- 차트 가독성 / 해석 카드 문구 검토

---

## 10. 배포/롤아웃 플랜 (Q8-24: 빅뱅)

### 10.1 cut-over 절차

```
T-7d   staging에서 Phase 1+2 백엔드 검증 완료
T-3d   staging에서 Phase 3 프론트 검증 완료
T-1d   prod DB 백업 (asset_master, price_daily 등 전체)
T-0    빅뱅 cut-over (수 분 다운타임)
       1. uvicorn 정지
       2. Alembic migration 실행 (5.1 SQL)
       3. 신규 자산 데이터 import (staging dump → prod)
       4. 새 코드 배포 (frontend + backend)
       5. uvicorn 재시작
       6. smoke test: /silver/compare 노출, KPI 산출 확인
T+1h   monitoring (Agentic chat tool, simulation API)
T+1d   사용자(본인) 직접 흐름 검토
T+7d   안정화 종료
```

### 10.2 rollback 전략

- Cut-over 직전 git tag (`v-bronze-final`) 생성
- 문제 발생 시 git revert + DB 백업 복원
- 예상 rollback 시간: 30분 이내

### 10.3 Bronze 마지막 상태 보존

- `feature/silver-rev1` branch에서 작업
- master로 merge 직전 `v-bronze-final` tag
- merge 후 master = Silver

---

## 11. 리스크 & 미해결 후속 과제

### 11.1 Part B 7대 허들 처리 매핑

| 허들 | 처리 |
|---|---|
| B-1 데이터 확장 | §2.1, §5.2, §7 (해소) |
| B-2 WBI 산식 | §2.5 (Q2-5/6 답변 반영, 해소) |
| B-3 환율 처리 | §2.3, §3.3, fx_daily 테이블 (Q1-3, Q3-7/8/9 답변, 해소) |
| B-4 캘린더 정렬 | §3 simulation에서 자산별 캘린더 + forward-fill (구현 시점 확정 필요, 부분 해소) |
| B-5 전략 모호성 | §3.4 (Q4-10~14 답변, 해소) |
| B-6 MDD 정의 | §3.7 (§11.2 lock + Q5-15 캘린더 연도, 해소) |
| B-7 운영 충돌 | §8 Phase, §10 cut-over (Q8-24/26 답변, 해소) |

### 11.2 Part C Gap Map 처리 매핑

| 카테고리 | 처리 |
|---|---|
| C-1 데이터/스키마 | §2, §5.1 |
| C-2 시뮬레이션 엔진 | §3 |
| C-3 UI/IA | §4, §6 |
| C-4 신호/지표 | §4.6 (단순화 유지), §3은 신호 미포함 |
| C-5 AI/Chat | §5.4 (Bronze Phase F 유지 + tool 정리) |
| C-6 인증/저장 | rev1 변경 없음 (Bronze 그대로 유지) |
| C-7 운영/배포 | §8, §10 |
| C-8 검증 | §9 |

### 11.3 미해결 / 후속 과제

- **C-2 fractional 정밀도**: 소수점 자릿수 미확정 (구현 시 12자리 가정, 추후 사용자 확인)
- **C-4 신호 빈도 기준**: silver-draft.md "3회/년" 가이드 폐기 여부 미확정 — rev1은 단순 단순화로 보류
- **Tab A 자산 정렬 캘린더**: 자산별 캘린더가 다를 때 차트 정렬 정책 (forward-fill 가정, 시각적 검증 필요)
- **시뮬레이션 결과 캐시**: 매 요청 재계산이 P95 latency 임계 초과하면 결과 캐시 도입 (Phase 5)
- **배당 데이터 정확화**: 공시 배당률 균등 분할 → 실제 배당락 데이터로 후속 교체
- **데이터 정합성 alerting**: 신규 8종에 alerting.py 확장 (Phase 1 후반)
- **Tab A·B·C 카드형 vs step형 결정**: §6.2 lock에 "시안 후 결정" — 실제 페이지 시안 후 사용자 검토
- **모바일 가로 스크롤 탭 vs hamburger**: 768px 미만 nav 동작 미확정

### 11.4 운영 리스크

- **빅뱅 다운타임**: 사용자 1명이라 영향 최소, but DB migration 실패 시 rollback 시간 30분 가정
- **JEPI 5년 padding**: cyclic returns 복제로 충분한지 시각적 검증 필요. 사용자 거부감 발생 시 padding 구간을 차트에서 회색 처리
- **Agentic tool 정리 누락**: strategy_classify/report 제거 시 LangGraph state machine fallback 동작 검증 필수

---

## 12. 부록 — 작업 체크리스트

### Phase 1 (Data Infra)

- [ ] Alembic migration 작성 (asset_master 컬럼 + fx_daily)
- [ ] SYMBOL_MAP 8종 추가 (QQQ/SPY/SCHD/JEPI/TLT/NVDA/GOOGL/TSLA)
- [ ] USD/KRW collector 작성
- [ ] 신규 자산 10년 backfill (staging)
- [ ] padding 알고리즘 unit test (JEPI fixture)
- [ ] WBI synthetic 시드 42 fixture 저장

### Phase 2 (Simulation Engine)

- [ ] `backend/research_engine/simulation/` 디렉터리 신규
- [ ] replay.py / strategy_a.py / strategy_b.py / portfolio.py
- [ ] padding.py / wbi.py / fx.py / mdd.py
- [ ] `routers/simulation.py` 작성
- [ ] `routers/fx.py` 작성
- [ ] integration test (Tab A/B/C)
- [ ] cross-check fixture (QQQ 10년)

### Phase 3 (Frontend)

- [ ] `pages/silver/CompareMainPage.tsx`
- [ ] `pages/silver/components/*` (10개 컴포넌트)
- [ ] `SignalDetailPage.tsx` (IndicatorSignalPage 단순화 후신)
- [ ] 모바일 반응형 (768px breakpoint)
- [ ] AssetPickerDrawer 동작

### Phase 4 (Cut-over)

- [ ] git tag `v-bronze-final`
- [ ] StrategyPage 코드 삭제, 테이블 drop migration
- [ ] DashboardPage/PricePage/CorrelationPage 코드 삭제
- [ ] Agentic tool registration 정리 (strategy_* 제거, simulation_* 추가)
- [ ] master merge + 빅뱅 배포
- [ ] smoke test
- [ ] 1주 monitoring

### Phase 5 (Stabilization)

- [ ] 사용자 피드백 수집
- [ ] 실제 배당락 데이터 도입 검토
- [ ] 시뮬레이션 결과 캐시 도입 검토
- [ ] 데이터 alerting 확장

---

**작성 종료 — 본 문서는 코딩 착수의 단일 source of truth.**
