# Session Compact

> Generated: 2026-02-12
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

## Current State

### Git
- Branch: `claude/review-project-status-pBqqS`
- Last commit: `1e35fd9` — [phase3-research] Step 3.4: 팩터 DB 저장
- origin에 push 완료

### Phase 3 진행률 — 33% (4/12)
| Task | Size | Status | Commit |
|------|------|--------|--------|
| 3.1 전처리 파이프라인 | M | ✅ Done | `d476c52` |
| 3.2 수익률+추세 팩터 | M | ✅ Done | `b1ce303` |
| 3.3 모멘텀+변동성+거래량 | M | ✅ Done | `b1ce303` |
| 3.4 팩터 DB 저장 | M | ✅ Done | `1e35fd9` |
| 3.5 전략 프레임워크 | M | ⬜ Next | — |
| 3.6 3종 전략 구현 | M | ⬜ | — |
| 3.7 시그널+DB 저장 | S | ⬜ | — |
| 3.8 백테스트 엔진 | L | ⬜ | — |
| 3.9 성과 평가 지표 | M | ⬜ | — |
| 3.10 백테스트 결과 DB | S | ⬜ | — |
| 3.11 배치 스크립트+통합 | M | ⬜ | — |
| 3.12 문서 갱신 | S | ⬜ | — |

### DB 현황
- price_daily: 5,559 rows (2023-02 ~ 2026-02)
- 자산별: KS200(732), 005930(732), 000660(732), SOXL(752), BTC(1097), GC=F(757), SI=F(757)

### 테스트 현황
- Unit: **122 passed** (기존 59 + 전처리 22 + 팩터 25 + factor_store 16)
- Integration: **4 passed** (INTEGRATION_TEST=1)
- 일반 pytest: 122 passed, 4 skipped
- ruff: All checks passed

## Remaining / TODO
- [ ] **배포 전**: `.env`에 실제 `ALERT_WEBHOOK_URL` 설정
- [ ] **Task 3.5~3.12**: Phase 3 나머지 구현
- [ ] **Phase 4: API** — FastAPI 조회 엔드포인트
- [ ] **Phase 5: Frontend** — React 시각화 대시보드

## Key Decisions
- [3.1] 크립토=일별 캘린더, 기타=영업일 캘린더 / 결측 ffill + 5% threshold
- [3.2-3.3] 15개 팩터 단일 파일 / RSI edge case 처리 (loss=0→100, gain=0→0)
- [3.2-3.3] Wilder smoothing: ewm(alpha=1/14) / MACD: ema_12 - ema_26
- [3.4] wide→long 변환 시 NaN 스킵, chunk_size=2000 UPSERT

## Context
다음 세션에서는 답변에 한국어를 사용하세요.
- **작업 디렉토리**: `backend/` 내에서 Python 작업 수행
- **venv**: `backend/.venv/Scripts/activate` (Windows), Python 3.12.3
- **dev-docs**: `dev/active/phase3-research/` (진행 중)
- **수집 스크립트**: `backend/scripts/collect.py` — `--start`, `--end`, `--assets` 인자
- **스케줄러**: `backend/scripts/daily_collect.bat` (수집 + healthcheck 자동 실행)
- **테스트**: `backend/tests/unit/` (122개) + `backend/tests/integration/` (4개)
- **마스터플랜**: `docs/masterplan-v0.md` — §7(분석 모듈 상세)
- Git remote: `https://github.com/bluecalif/stock-dashboard.git`
- Railway PostgreSQL 연결됨

## Next Action
1. **Task 3.5**: 전략 프레임워크 — Strategy ABC, 공통 체결 규칙
2. **Task 3.6**: 3종 전략 구현 (모멘텀/추세/평균회귀)
3. **Task 3.7**: 시그널 생성 + DB 저장
4. **Task 3.8~3.10**: 백테스트 + 성과 지표 + 결과 DB 저장
