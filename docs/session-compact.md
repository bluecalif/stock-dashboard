# Session Compact

> Generated: 2026-02-12 (updated)
> Source: Conversation compaction via /compact-and-go

## Goal
Phase 3 research_engine 구현 (팩터/전략/백테스트)

## Completed
- [x] **Phase 2 전체 완료** (Task 2.1 ~ 2.10, 100%)
- [x] **Phase 3 dev-docs 생성**: `dev/active/phase3-research/` (plan, context, tasks)
- [x] **Task 3.1**: 전처리 파이프라인 (`d476c52`)
  - `preprocessing.py`: load_prices, align_calendar, check_missing, flag_outliers
  - 영업일/일별 캘린더 정렬, ffill + threshold 검증, 이상치 z-score 플래그
  - 테스트 22개 신규
- [x] **Task 3.2-3.3**: 15개 팩터 생성 (`b1ce303`)
  - `factors.py`: compute_all_factors() + 개별 팩터 함수
  - 수익률(4), 추세(6), 모멘텀(2), 변동성(2), 거래량(1)
  - RSI Wilder smoothing + edge case 처리
  - 테스트 25개 신규
- [x] **Task 3.4**: 팩터 DB 저장 (`1e35fd9`)
  - `factor_store.py`: _factors_to_records (wide→long, NaN 스킵), _upsert_factors (ON CONFLICT)
  - store_factors_for_asset: preprocess→compute→UPSERT 파이프라인
  - store_factors_all: 전 자산 오케스트레이션
  - 테스트 16개 신규
- [x] **Task 3.5-3.7**: 전략 엔진 + 시그널 저장 (`6956015`)
  - `strategies/base.py`: Strategy ABC, SignalResult dataclass, next-day execution rule
  - `strategies/momentum.py`: ret_63d + vol_20 기반 모멘텀 전략
  - `strategies/trend.py`: SMA20/60 골든/데드크로스 추세 전략
  - `strategies/mean_reversion.py`: z-score 밴드 이탈/복귀 평균회귀 전략
  - `strategies/__init__.py`: STRATEGY_REGISTRY + get_strategy()
  - `signal_store.py`: DELETE+INSERT 방식 idempotent 시그널 저장
  - 테스트 43개 신규 (전략 30 + 시그널 저장 13)

## Current State

### Git
- Branch: `claude/update-docs-steps-complete-4ccpm`
- Last commit: `6956015` — [phase3-research] Step 3.5-3.7: 전략 엔진 + 시그널 저장 (Stage B)
- origin에 push 완료

### Phase 3 진행률 — 58% (7/12)
| Task | Size | Status | Commit |
|------|------|--------|--------|
| 3.1 전처리 파이프라인 | M | ✅ Done | `d476c52` |
| 3.2 수익률+추세 팩터 | M | ✅ Done | `b1ce303` |
| 3.3 모멘텀+변동성+거래량 | M | ✅ Done | `b1ce303` |
| 3.4 팩터 DB 저장 | M | ✅ Done | `1e35fd9` |
| 3.5 전략 프레임워크 | M | ✅ Done | `6956015` |
| 3.6 3종 전략 구현 | M | ✅ Done | `6956015` |
| 3.7 시그널+DB 저장 | S | ✅ Done | `6956015` |
| 3.8 백테스트 엔진 | L | ⬜ Next | — |
| 3.9 성과 평가 지표 | M | ⬜ | — |
| 3.10 백테스트 결과 DB | S | ⬜ | — |
| 3.11 배치 스크립트+통합 | M | ⬜ | — |
| 3.12 문서 갱신 | S | ⬜ | — |

### DB 현황
- price_daily: 5,559 rows (2023-02 ~ 2026-02)
- 자산별: KS200(732), 005930(732), 000660(732), SOXL(752), BTC(1097), GC=F(757), SI=F(757)

### 테스트 현황
- Unit: **165 collected** (기존 59 + 전처리 22 + 팩터 25 + factor_store 16 + 전략 30 + signal_store 13)
- Integration: **4 passed** (INTEGRATION_TEST=1)
- ruff: All checks passed

## Remaining / TODO
- [ ] **배포 전**: `.env`에 실제 `ALERT_WEBHOOK_URL` 설정
- [ ] **Task 3.8~3.12**: Phase 3 나머지 구현 (Stage C + D)
- [ ] **Phase 4: API** — FastAPI 조회 엔드포인트
- [ ] **Phase 5: Frontend** — React 시각화 대시보드

## Key Decisions
- [3.1] 크립토=일별 캘린더, 기타=영업일 캘린더 / 결측 ffill + 5% threshold
- [3.2-3.3] 15개 팩터 단일 파일 / RSI edge case 처리 (loss=0→100, gain=0→0)
- [3.2-3.3] Wilder smoothing: ewm(alpha=1/14) / MACD: ema_12 - ema_26
- [3.4] wide→long 변환 시 NaN 스킵, chunk_size=2000 UPSERT
- [3.5] Strategy ABC + SignalResult dataclass / next-day open 체결 규칙
- [3.6] 3종 전략: 모멘텀(ret_63d+vol_20), 추세(SMA 골든크로스), 평균회귀(z-score 밴드)
- [3.7] signal_daily DELETE+INSERT 방식 (UPSERT 대신) — PK 구조에 최적

## Context
다음 세션에서는 답변에 한국어를 사용하세요.
- **작업 디렉토리**: `backend/` 내에서 Python 작업 수행
- **venv**: `backend/.venv/Scripts/activate` (Windows), Python 3.12.3
- **dev-docs**: `dev/active/phase3-research/` (진행 중)
- **수집 스크립트**: `backend/scripts/collect.py` — `--start`, `--end`, `--assets` 인자
- **스케줄러**: `backend/scripts/daily_collect.bat` (수집 + healthcheck 자동 실행)
- **테스트**: `backend/tests/unit/` (165개) + `backend/tests/integration/` (4개)
- **마스터플랜**: `docs/masterplan-v0.md` — §7(분석 모듈 상세)
- Git remote: `https://github.com/bluecalif/stock-dashboard.git`
- Railway PostgreSQL 연결됨

## Next Action
1. **Task 3.8**: 백테스트 엔진 — 단일/다중 자산, equity curve, trade log
2. **Task 3.9**: 성과 평가 지표 — CAGR, MDD, Sharpe, Sortino, Calmar
3. **Task 3.10**: 백테스트 결과 DB 저장
4. **Task 3.11~3.12**: 배치 스크립트 + 통합 테스트 + 문서 갱신
