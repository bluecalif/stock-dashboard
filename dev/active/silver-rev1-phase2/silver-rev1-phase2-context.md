# Phase 2 Context — 시뮬레이션 엔진
> Gen: silver
> Last Updated: 2026-05-10
> Status: Planning

## 0. 핵심 원칙 — "Show, don't claim"

> **검증 게이트의 체크박스는 evidence가 `verification/step-N-<topic>.md`에 paste되고 사용자가 본 후에만 표시 가능.**
> Claude의 "PASS / 통과" 주장만으로는 mark complete 금지.

게이트 3단 형식 (전 step 공통):
```
- [ ] <검증 항목>
  - 명령: <실행 가능한 1줄>
  - Evidence: <형식 + paste 위치>
  - 통과 기준: <구체 임계>
```

수치/시계열/분포 step은 PNG 의무 → `verification/figures/step-N-<topic>.png`

## 1. 핵심 파일

### 1.1 읽어야 할 기존 코드/문서

| 파일 | 용도 |
|---|---|
| `docs/silver-masterplan.md` §3 | 시뮬레이션 엔진 전체 명세 — 단일 SoT |
| `docs/silver-masterplan.md` §5.3 | API 라우터 변경 (신규/제거/유지) |
| `dev/active/project-overall/project-overall-context.md` D-4~D-17 | Phase 2 직결 결정 lock |
| `backend/research_engine/simulation/padding.py` | Phase 1 완성 — replay.py에서 import |
| `backend/research_engine/simulation/wbi.py` | Phase 1 완성 — replay.py에서 import |
| `backend/db/models/` | AssetMaster(annual_yield, currency), FxDaily |
| `backend/api/main.py` | 라우터 등록 위치 (`include_router`) |
| `backend/api/routers/` | 신규 simulation.py, fx.py 추가 위치 |

### 1.2 Phase 1 산출물 (즉시 재사용)

| 산출물 | 경로 | 재사용 방식 |
|---|---|---|
| cyclic padding | `simulation/padding.py::pad_returns()` | replay.py에서 `from .padding import pad_returns` |
| WBI synthetic | `simulation/wbi.py::generate_wbi()` | replay.py WBI 경로에서 호출 |
| JEPI fixture | `fixtures/jepi_5y_returns.npy` | test_replay.py fixture |
| WBI fixture | `fixtures/wbi_seed42_10y.npz` | test_replay.py fixture |

## 2. 데이터 인터페이스

```
[DB: fx_daily] ──→ fx.py::load_fx_series(start, end)
                    → pd.Series(index=date, value=usd_krw_close, forward-filled)
                    → replay.py / strategy_a.py

[DB: price_daily] ──→ replay.py::_load_prices(asset_code, start, end)
                       → pd.Series(index=date, value=close, forward-filled)

[DB: asset_master] ──→ annual_yield → replay.py D-4 배당 계산
                        currency    → fx 환산 분기

simulation/ ─┬─ replay.py      ──→ POST /v1/silver/simulate/replay
             ├─ strategy_a.py  ──┐
             ├─ strategy_b.py  ──┼─→ POST /v1/silver/simulate/strategy
             ├─ portfolio.py   ──→ POST /v1/silver/simulate/portfolio
             └─ mdd.py         ──→ (replay/strategy/portfolio 공통 KPI 호출)

[DB: fx_daily] ──→ GET /v1/fx/usd-krw → JSON {date, usd_krw_close}[]
```

**SimInput Pydantic schema** (마스터플랜 §3.2):
```python
class SimInput(BaseModel):
    asset_codes: list[str]          # Tab A: 최대 6종, Tab B: 3종, Tab C: preset
    monthly_amount: int             # KRW 단위 (UI에서 만원 × 10000)
    period_years: Literal[3, 5, 10]
    base_currency: Literal["KRW", "local"] = "KRW"
```

**SimResult 공통 구조**:
```python
class EquityPoint(BaseModel):
    date: date
    krw_value: float
    local_value: float | None   # USD 자산만

class KpiResult(BaseModel):
    final_asset_krw: float
    total_return: float         # (final - deposit) / deposit
    annualized_return: float    # (final/deposit)^(1/years) - 1
    yearly_worst_mdd: float     # 캘린더 연도 최악 MDD (음수)
```

## 3. 핵심 결정사항 (Phase 2 코딩 직결)

| # | 결정 | 코딩 영향 |
|---|---|---|
| D-4 | 배당 = `annual_yield / 252` × 보유평가액 (매 거래일) | `replay.py`: `shares *= (1 + annual_yield/252)` |
| D-6 | 트리거 = **현지통화 가격** 기준 | `strategy_a.py` 60거래일 ratio: USD 자산은 USD 가격 |
| D-7 | 강제 재매수 = 매도일 + **365일** | `forced = date >= sell_date + timedelta(days=365)` |
| D-8 | lock = **재매수 시점** 연도 | `lock_until_year = reentry_date.year` (매도 시점 X) |
| D-9 | grace period = **12개월** | `grace_end = period_start + relativedelta(months=12)` |
| D-10 | MDD = **캘린더 연도** 기준 | `mdd.py` Jan-Dec 슬라이스 |
| D-16 | 이벤트 순서: **정기 적립 먼저** → `strategy.step()` | `replay.py` 루프에서 적립 후 strategy 호출 |
| D-17 | KPI 4종 fix | `compute_kpi()` 시그니처 불변 |
| D-18 | Tab A universe = QQQ/SPY/KS200/SCHD/JEPI/WBI **6종** | SimInput validator |
| D-19 | Tab B 자산 = QQQ/SPY/KS200 **3종만** | SimInput validator |
| D-20 | Tab C preset = **4개 고정** | preset 상수 dict |
| C-2 | fractional 정밀도 = float64 | **미확정** — Phase 2 중 사용자 확인 필요 |

## 4. 컨벤션 체크리스트

### 4.1 코드
- 인코딩: `encoding='utf-8'` 명시 (파일 I/O 시)
- int overflow: `astype("int64")` (int32 max = 2,147,483,647 — NVDA 교훈)
- pytest: `backend/tests/unit/` 위치, fixture는 `conftest.py` 또는 함수 내 정의

### 4.2 아키텍처 — Router-Service-Repo 패턴
```
routers/simulation.py    → FastAPI route 정의, Pydantic I/O
services/simulation_service.py → 비즈니스 로직 조율 (DB 조회 + simulation 호출)
research_engine/simulation/  → 순수 계산 모듈 (DB 미포함)
```

### 4.3 커밋
- 형식: `[silver-rev1-phase2] Step X.Y: description`
- 체크박스 flip은 evidence paste + 사용자 확인 후

### 4.4 서버 실행
```bash
cd /c/Users/User/Projects-2026/active/stock-dashboard/backend
uvicorn api.main:app --reload
```
좀비 프로세스 시: `tasklist | grep python` → `taskkill //F //PID <pid>` 전부 종료

## 5. 미해결 후속 결정

| 항목 | 결정 시점 | 현재 가정 |
|---|---|---|
| C-2 fractional 정밀도 자릿수 | Phase 2 코딩 중 사용자 확인 | float64 |
| Tab A 캘린더 forward-fill 방향 | Phase 2 시각 검증 (G3 PNG) | KR→US 방향 forward-fill |
| P95 latency 임계 | Phase 5 | 캐시 없음 (매 요청 재계산) |
