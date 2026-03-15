# Session Compact

> Generated: 2026-03-15
> Source: Phase D-rev DR.1~DR.9 구현 완료 + push

## Goal
Phase D-rev 피드백 반영 — 전략(momentum/trend/mean_reversion) 기반 → 개별 지표(RSI/MACD/ATR+vol) 기반 전환, 탭 통합, 레이아웃 개선, 정규화 버그 수정

## Completed
- [x] DR.1 지표별 시그널 생성 서비스 (`indicator_signal_service.py` 신규) — RSI 30/70 교차, MACD histogram 부호전환, ATR+vol 고변동성 구간 감지
- [x] DR.2 지표별 성공률 계산 수정 — `compute_indicator_accuracy()` 추가, on-the-fly 시그널 기반
- [x] DR.3 지표 비교 서비스 수정 — `compare_indicators()` RSI vs MACD 비교, `DEFAULT_INDICATOR_IDS`
- [x] DR.4 API 엔드포인트 수정 — `/indicator-signals` 신규, `/signal-accuracy` indicator_id 파라미터, `/indicator-comparison` mode=indicator|strategy
- [x] DR.5 3탭→2탭 전환 — IndicatorSignalPage 전면 수정 (시그널/성공률), 전략 배제
- [x] DR.6 시그널 탭 레이아웃 — grid 3/4+1/4, ReferenceLine 수직 점선 (B/S 라벨)
- [x] DR.7 성공률 탭 레이아웃 — grid 3/4+1/4, 지표별 요약 패널
- [x] DR.8 정규화 버그 수정 — undefined 유지, 0 스파이크 방지
- [x] DR.9 ATR 특수 처리 — ReferenceArea 고변동성 구간 표시
- [x] 커밋 `9073f05` + push 완료 (Railway/Vercel 자동 배포)
- [x] DR.11 오버레이 지표 표시 + MACD 시그널라인 — IndicatorSignalPage에서 factor 시계열 fetch → 차트에 지표 곡선 오버레이, 시그널 이력에 지표값 표시

## Current State

### Git 상태
- 최신 커밋: `9073f05` (master, DR.1~DR.9 포함, push 완료)
- 미커밋 변경: dev-docs(project-overall), docs/session-compact.md, untracked 파일들

### 테스트 상태
- Backend: **678 tests** passed, 7 skipped, ruff clean
- Frontend: tsc --noEmit 0 errors, vite build 성공

### 인프라 상태
- **Railway**: `https://backend-production-e5bc.up.railway.app` — 배포 진행 중
- **Vercel**: `https://stock-dashboard-alpha-lilac.vercel.app` — 배포 진행 중

### Changed Files (이번 세션)
**Backend 신규:**
- `backend/api/services/analysis/indicator_signal_service.py` — on-the-fly 시그널 생성
- `backend/tests/unit/test_indicator_signal_service.py` — 18 tests

**Backend 수정:**
- `backend/api/services/analysis/signal_accuracy_service.py` — compute_indicator_accuracy 추가
- `backend/api/services/analysis/indicator_comparison.py` — compare_indicators 추가
- `backend/api/routers/analysis.py` — 3 엔드포인트 수정/추가
- `backend/api/schemas/analysis.py` — IndicatorSignalItem, V2 스키마 추가
- `backend/tests/unit/test_signal_accuracy.py` — DR.2 테스트 4건 추가
- `backend/tests/unit/test_indicator_comparison.py` — DR.3 테스트 4건 추가
- `backend/tests/unit/test_api/test_analysis_router.py` — DR.4 테스트 전면 수정

**Frontend 수정:**
- `frontend/src/types/api.ts` — IndicatorSignalItem, V2 타입 추가
- `frontend/src/api/analysis.ts` — fetchIndicatorSignals, fetchIndicatorAccuracy, fetchIndicatorComparisonV2
- `frontend/src/pages/IndicatorSignalPage.tsx` — 3탭→2탭 전면 개편
- `frontend/src/components/charts/IndicatorOverlayChart.tsx` — 시그널 점선 + ATR 구간 + null 안전 처리

## Remaining / TODO
- [ ] DR.10 Phase D-rev 통합 검증 — 프로덕션 배포 후 브라우저 E2E 확인
  1. 2탭 구조 (시그널/성공률) 확인
  2. RSI/MACD/ATR 지표 선택 → 시그널 표시
  3. 시그널 수직 점선 표시
  4. 3/4 + 1/4 레이아웃 (시그널 탭, 성공률 탭)
  5. 성공률 비교 순위 테이블 (RSI vs MACD)
  6. 정규화 시 0으로 튀지 않음
  7. ATR 위험 구간 표시
  8. 챗봇 연동 동작
  9. **지표 오버레이** — RSI 곡선, MACD+시그널 라인, ATR+변동성 라인 가격 위 오버레이 확인
  10. **시그널 이력 패널** — 지표값 수치 표시 확인
- [ ] Phase E 전략 페이지 구현 (D-rev 완료 후)

## Key Decisions
- **on-the-fly 시그널 생성**: factor_daily에서 파생, DB 저장 없음 (indicator_signal_service.py)
- **전환점(transition) 감지**: 단순 임계값이 아닌 이전일→당일 교차 여부로 판단
- **기존 strategy API 하위호환**: strategy_id 파라미터 유지, indicator_id와 택일
- **ATR+vol 통합**: "atr_vol" indicator_id로 묶어 처리, 성공률은 RSI/MACD만
- **indicator-comparison 모드**: mode=indicator(기본) vs mode=strategy(하위호환)
- **response_model 제거**: indicator-comparison에서 Union 타입 반환 위해 response_model 제거, return type annotation 사용

## Context
- 다음 세션에서는 답변에 한국어를 사용하세요.
- **기존 코드 패턴**: Router-Service-Repository 3계층, 함수형 repo, Pydantic v2, SQLAlchemy 2.0 Mapped
- **Frontend**: React 19 + Vite + TypeScript + Tailwind + axios + react-router-dom v6 + zustand + Recharts
- **SSE 주의**: EventSource(GET) 사용 금지 → fetch + ReadableStream 사용
- **피드백 원본**: `docs/post-mvp-feedback.md` (Phase C/D/E 피드백 모두 포함)
- **Phase D-rev 계획**: `dev/active/phaseD-revision/` dev-docs 참조
- **프로덕션 API**: insufficient_data 응답은 DB 데이터 부족 문제이지 API 오류 아님

## Project Status

| Phase | 상태 | 비고 |
|-------|------|------|
| MVP (0~7) | ✅ 완료 | 83/83 tasks |
| Phase A Auth | ✅ 완료 | 16/16 tasks |
| Phase B Chatbot | ✅ 완료 | 19/19 tasks |
| Phase C 상관도 | ✅ 완료 | 12/12 Steps |
| Phase C-rev 피드백 | ✅ 완료 | 7/7 Tasks |
| Phase C-rev2 피드백 | ✅ 완료 | 4/4 Tasks + 품질 개선 |
| Phase D 지표 | ✅ 완료 | 12/12 Tasks |
| Phase D-rev 피드백 | 🔄 진행 중 | 10/11 Tasks (DR.10 검증 남음) |
| Phase E 전략 | ⬜ 미시작 | 9 Steps |
| Phase F~G | ⬜ 미시작 | Memory/Onboarding |

## Next Action
1. **DR.10 통합 검증** — 프로덕션 배포 완료 확인 후 REST API 테스트 + 브라우저 E2E 체크리스트 수행
2. Phase E 전략 페이지 (D-rev 완료 후)
