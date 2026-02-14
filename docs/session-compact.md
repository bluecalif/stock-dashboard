# Session Compact

> Generated: 2026-02-14 20:30
> Source: Conversation compaction via /compact-and-go

## Goal
Phase 5 Frontend UX 디버깅 완료 (Step 5.13) → UX 재확인 → 커밋 → Phase 6 착수

## Completed
- [x] **Step 5.1~5.12**: 프론트엔드 전체 구현 + UX 버그 수정 (이전 세션)
- [x] **Step 5.13-1: Missing Threshold 수정**
  - `factor_store.py`: `store_factors_for_asset()`에 `missing_threshold` 파라미터 추가
  - `run_research.py`: `store_factors_for_asset()` 및 `preprocess()` 호출에 `missing_threshold=0.10` 전달
  - KS200/005930/000660 Factor/Signal/Backtest 전체 생성 성공
- [x] **Step 5.13-2: Backtest store_failed 수정**
  - `backtest_store.py`: `_to_date()`, `_to_float()` 헬퍼 추가 → numpy/Timestamp → Python native 변환
  - 전 자산 12개 백테스트 run 저장 성공
- [x] **Step 5.13-3: CORS 차단 수정**
  - `api/main.py`: `allow_origins`에 `localhost:5174`, `127.0.0.1:5174` 추가
- [x] **Step 5.13-4: NaN JSON Serialization 수정**
  - `api/schemas/signal.py`: `score` 필드에 `nan_to_none` field_validator 추가
  - `api/schemas/factor.py`: `value` 필드를 `float | None`으로 변경 + 동일 validator 추가
- [x] **파이프라인 재실행**: 전체 7개 자산 × 3개 전략 = 21개 조합 완료
- [x] **디버그 히스토리 문서화**: `dev/active/phase5-frontend/debug-history.md` 생성

## Current State

### 프로젝트 진행률
| Phase | 상태 | Tasks |
|-------|------|-------|
| 1-4 (Skeleton~API) | ✅ 완료 | 46/46 |
| 5 Frontend | 🔧 UX 재확인 중 | 12.5/13 |
| 6 Deploy & Ops | 미착수 | 0/16 |

### UX 버그 현황
| # | 페이지 | 이슈 | 상태 |
|---|--------|------|------|
| 1 | Home | MiniChart X축 역순 | ✅ 수정 |
| 2 | Price | Gold/Silver Network Error | ✅ 수정 |
| 3 | Price | 거래량 미표시 | ✅ 수정 |
| 4 | Factor | KS200/005930/000660 미표시 | ✅ 파이프라인 수정 완료 |
| 5 | Signal | X축 역순 | ✅ 수정 |
| 6 | Signal | 마커 설명 없음 | ✅ 수정 |
| 7 | Signal | 관망/무신호 구분 불가 | ✅ 수정 |
| 8 | Signal | 추세추종 미표시 | ✅ 수정 |
| 9 | Signal | 평균회귀 마커만 표시 | ⚠️ mean_reversion에서 `close` 컬럼 누락 워닝 → 시그널 0개 생성 (별도 조사 필요) |
| 10 | Strategy | 전체 미표시 | ✅ 백테스트 데이터 생성 완료 |
| 11 | Dashboard | 백테스트 상태 배지 | ✅ 수정 |

### 파이프라인 실행 결과 (2026-02-14)
| 자산 | Factor | Momentum | Trend | Mean Reversion |
|------|--------|----------|-------|----------------|
| KS200 | ✅ 4017 | CAGR 72.6% | CAGR 89.8% | CAGR 6.4% |
| 005930 | ✅ 4017 | CAGR 79.6% | CAGR 144.1% | CAGR 3.4% |
| 000660 | ✅ 4017 | CAGR 30.6% | CAGR 183.1% | CAGR 12.7% |
| SOXL | ✅ 4002 | CAGR 0.0% | CAGR 242.5% | CAGR -22.9% |
| BTC | ✅ | CAGR -1.7% | CAGR -11.0% | CAGR -9.4% |
| GC=F | ✅ | CAGR 33.9% | CAGR 50.9% | CAGR 1.3% |
| SI=F | ✅ | CAGR 32.3% | CAGR 84.9% | CAGR 7.4% |

### Changed Files (이번 세션)
```
backend/
├── api/
│   ├── main.py                    — CORS: 5174 포트 추가
│   └── schemas/
│       ├── signal.py              — score NaN→None field_validator
│       └── factor.py              — value NaN→None field_validator, float→float|None
├── research_engine/
│   ├── backtest_store.py          — _to_date(), _to_float() 헬퍼 + 타입 변환
│   └── factor_store.py            — missing_threshold 파라미터 추가
└── scripts/
    └── run_research.py            — missing_threshold=0.10 전달

dev/active/phase5-frontend/
└── debug-history.md               — 신규 생성 (디버그 히스토리)
```

### Git / Tests
- Branch: `master`, **커밋 안 됨** (프론트+백엔드 수정사항 전부 미커밋)
- TSC: 미확인 (이번 세션에서 프론트엔드 파일은 변경 안 함)

## Remaining / TODO
- [ ] **UX 재확인**: 사용자가 `docs/front-UX-check.md` 2차 결과 작성 중 — 시그널 페이지 모멘텀 Network Error는 수정 완료, 다른 페이지 결과 대기
- [ ] **Bug #9 조사**: mean_reversion 전략에서 `close` 컬럼 누락 워닝 → 시그널 0개 생성 원인 파악
- [ ] **커밋**: Step 5.11~5.13 프론트+백엔드 전체 수정사항
- [ ] **Phase 6 (Deploy & Ops) 착수**

## Key Decisions
- **missing_threshold 10%**: 한국주식(KS200/005930/000660) 공휴일 캘린더 차이로 6.7% 결측 → 10%로 상향
- **NaN 방어**: DB에서 NaN이 올 수 있으므로 API 스키마 레벨에서 field_validator로 None 변환
- **CORS 포트 범위**: Vite 포트 충돌 대비 5173 + 5174 둘 다 등록
- **전략 ID**: 백엔드 STRATEGY_REGISTRY = `momentum`, `trend`, `mean_reversion`
- **uvicorn --reload 불안정**: Windows WatchFiles 리로더 신뢰 불가 → 코드 변경 시 수동 재시작

## Context
다음 세션에서는 답변에 한국어를 사용하세요.
- **작업 디렉토리**: `frontend/` (React SPA) + `backend/` (파이프라인/API)
- **venv**: `backend/.venv/Scripts/activate` (Windows), Python 3.12.3
- **Bash 경로**: `/c/Projects-2026/stock-dashboard` (Windows 백슬래시 불가)
- **UX 체크 결과**: `docs/front-UX-check.md` (사용자 2차 작성 중)
- **디버그 히스토리**: `dev/active/phase5-frontend/debug-history.md`
- **서버 포트**: Backend `localhost:8000`, Frontend `localhost:5174` (5173 충돌 시)
- **mean_reversion 워닝**: `Missing 'close' column for mean_reversion` — 전 자산 공통, 시그널 0개지만 백테스트는 별도 실행됨
- Git remote: `https://github.com/bluecalif/stock-dashboard.git`
- **커밋 안 됨**: 프론트엔드 6개 + 백엔드 6개 + dev 1개 = 총 13개 파일 수정/생성 상태

## Next Action
1. **UX 재확인 계속**: 사용자에게 브라우저에서 전체 페이지 테스트 요청 (서버는 이미 구동 중)
2. `docs/front-UX-check.md` 2차 결과에 따라 추가 수정
3. Bug #9 (mean_reversion close 컬럼) 조사 및 수정
4. 전체 수정사항 커밋
5. Phase 6 착수
