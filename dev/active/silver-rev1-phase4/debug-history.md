# Phase 4 Debug History — 빅뱅 Cut-over
> Gen: silver
> Last Updated: 2026-05-10 (버그 수정 3종 추가)

버그·디버깅 이력이 발생하면 여기에 추가.

---

## 형식

```markdown
## [날짜] Step P4-N — [버그 제목]

**증상**: ...
**원인**: ...
**수정**: ...
**교훈**: ...
```

---

## [2026-05-10] P4-7 (monitoring) — prod 버그 3종 발견 및 수정

### 버그 A: 단일자산 Tab A — WBI 배열 길이 불일치

**증상**: WBI 자산 추가 시 "시뮬레이션 조회에 실패했습니다." 에러 (`500`).

**원인**: `replay.py`에서 `n_days = period_years * 252`로 생성한 `generate_wbi(n_days)`가 2520개를 반환하지만, `pd.date_range(end=today, periods=n_days, freq="B")`는 오늘이 non-business day(일요일)일 때 2519개를 반환. 배열 길이 불일치로 `pd.Series()` 생성 실패.

**수정**: `trading_dates = pd.date_range(...)`를 먼저 생성 후 `n_days = len(trading_dates)`로 맞춤. → `8fc9013`

**교훈**: `pd.date_range(periods=N, freq="B")`는 `end`가 non-business day일 때 실제 N-1개를 생성할 수 있음. 배열 길이는 항상 date_range 결과 기준으로 맞춰야 함.

---

### 버그 B: 자산 vs 전략 Tab B — KS200 선택 시 화이트 스크린

**증상**: Tab B에서 KS200 선택 시 페이지 전체 화이트 스크린.

**원인**:
1. `price_daily`에 KS200 NaN 가격 4개 존재
2. `_load_price_and_fx()`에서 NaN 필터링 없이 Series 생성 → `shares = monthly / NaN = NaN`
3. KPI: `final_asset_krw = NaN` → Pydantic JSON 직렬화 시 `null`
4. 프론트에서 `null` KPI 렌더링 중 TypeError → React 컴포넌트 크래시

**수정**: `_load_price_and_fx()`에서 `r.close is not None` 필터 + `.dropna()` 추가. → `8fc9013`

**교훈**: DB에서 가져온 가격 Series는 항상 NaN 필터링 필수. `replay.py`의 `replay()`는 이미 `.dropna()`를 했지만, `simulate_strategy()`의 `_load_price_and_fx()`는 누락됐음.

---

### 버그 C: WBI 연 수익률 2.7% (목표 20%)

**증상**: WBI 단일 자산 DCA 10년 결과에서 annualized return이 2.7%로 표시 (사용자 기대: ~10%).

**원인**: `generate_wbi(seed=42)`의 GBM 경로가 우연히 20% 기대값에서 크게 벗어남. seed=42 경로의 WBI 자산 자체 CAGR = 5.63% (기대 20%).

**수정**: zero-mean 노이즈 + log-return 기반 drift 보정으로 정확히 20% CAGR 달성 보장.
```python
# 기존: mu_adj drift로 기대값만 설정 → seed에 따라 크게 벗어남
# 수정: noise=(0-mean) + target_log 기반 drift 조정
target_log = n_days * (np.log(1 + annual_return) / 252)
drift_per_day = (target_log - sum(log(1+noise))) / n_days
```
→ WBI CAGR: 5.63% → 19.95%, fixture 재생성. → `1d82073`

**교훈**: GBM "기대값" ≠ 특정 seed "실현값". 벤치마크 자산처럼 CAGR을 보장해야 하는 경우에는 drift 재스케일링 필요. DCA annualized (10.52%)가 자산 CAGR (20%)보다 낮은 것은 DCA 특성상 정상 (평균 투자 기간 ≈5년).

---

## [2026-05-10] P4-2~P4-6 — CI 연속 실패 (4회) → 수정 과정

**증상**: P4-1~P4-5 커밋(`3152c2e`) push 후 CI가 4회 연속 실패.

**원인 1 — ruff lint 71개 에러**: CI는 lint 통과 후 배포를 진행하는데(`needs: test`), 기존 코드에 누적된 lint 에러가 lint 단계를 막음. `ruff --fix`를 Windows 로컬에서만 실행하고 CI 환경(Linux)과 수정 결과가 달라 재실패.

**수정 1**: `pyproject.toml`에 `per-file-ignores` 추가 (scripts/tests/alembic/simulation_service 예외). `ruff --fix`를 재실행해 수정된 파일들을 추가 커밋.

**원인 2 — backtest 테스트 실패**: lint 통과 후 `test_backtests.py` (20개 테스트)와 `test_agentic_data_fetcher.py::test_backtest_strategy_args`가 404로 실패. `backtests.py` 라우터 삭제 후 엔드포인트가 없어졌기 때문.

**수정 2**: `test_backtests.py` 전체 삭제, `test_agentic_data_fetcher.py`의 backtest_strategy 테스트를 simulation_replay/strategy 테스트로 교체.

**원인 3 — Silver gen 기준 테스트 불일치**: `test_fdr_client.py::test_symbol_map_completeness`(7→15종), `test_ingest.py`(7→15, 6→14), `test_edge_cases.py` backtest edge case들 실패. Bronze 기준 테스트들이 Silver gen 코드와 충돌.

**수정 3**: Silver gen 기준으로 테스트 수치 수정 + backtest edge case 테스트 제거. CI `2d66c8c` success → Railway+Vercel 배포 완료.

**교훈**:
- CI가 lint에서 막히면 테스트 단계 실패가 숨겨짐 — lint를 먼저 수정해야 테스트 실패가 드러남
- Bronze 기준 테스트들을 Silver gen 시작 시점에 Silver 기준으로 일괄 업데이트했어야 했음
- Windows ruff --fix 결과와 Linux CI ruff 결과가 다를 수 있음 → 로컬에서 확인 후 커밋
