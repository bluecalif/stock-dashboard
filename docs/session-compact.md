# Session Compact

> Generated: 2026-03-16
> Source: Phase D-improve 7/7 완료 (DI.1~DI.7)

## Goal
Phase D 추가 개선 Point 반영 — 시그널 frequency 제어(T+3), RSI 해제 신호, ATR 스케일 개선, 성공률 탭 기간 동기화, 지표 설명/기준 표시

## Completed
- [x] DI.1 지표 설명 및 판정 기준 표시
  - `INDICATOR_DESCRIPTIONS` 상수, 시그널 패널 상단 설명 카드
- [x] DI.2 T+3 시그널 frequency 제어
  - `_apply_frequency_filter()` 추가 — 방향 무관, 마지막 시그널로부터 min_gap_days 이내 제거
  - API `min_gap_days` 파라미터 (기본 3, 0=비활성)
  - 성공률 서비스에도 동일 파라미터 전달
  - 테스트 5건 추가
- [x] DI.3 RSI 해제 신호 추가
  - `signal=2` (매수해제=과매도 탈출), `signal=-2` (매도해제=과매수 탈출)
  - 성공률 계산에서 `signal in (1, -1)`만 평가 (해제/경고 제외)
  - 프론트: 해제 배지(파란/주황), 차트 "X" 마커
  - 테스트 3건 추가
- [x] DI.4 ATR+변동성 스케일 개선
  - 프론트: atr_14를 `(atr_14/close)*100` %, vol_20을 `*100` %로 변환
  - 참조선: ATR 3%, 변동성 30% (ReferenceLine)
  - 백엔드: label에 트리거 지표 명시 ("ATR 3.2% + 변동성 35.0%")
- [x] DI.5 성공률 탭 기간 동기화
  - `/signal-accuracy`, `/indicator-comparison`에 `start_date`, `end_date` 파라미터 추가
  - `compare_indicators()`에 기간 + min_gap_days 전달
  - 프론트: DateRangePicker 공유 (두 탭 동일 기간)
- [x] DI.6 성공률 데이터 매칭 + 기준 설명
  - 요약 패널에 "예측 기간: T+N일", "성공 기준: 매수→상승, 매도→하락" 설명 카드
- [x] DI.7 MACD signal lookback 검증
  - DR.12 LOOKBACK_DAYS=150 확장으로 해결 확인, 추가 변경 불필요

## Current State

### Git 상태
- 최신 커밋: `d942cfc` (master, DR.12까지 push 완료)
- 미커밋 변경: DI.1~DI.7 전체 (커밋 대기)

### 테스트 상태
- Backend: **689 tests** passed, 7 skipped, ruff clean
- Frontend: tsc --noEmit 0 errors, vite build 성공

### 인프라 상태
- **Railway**: `https://backend-production-e5bc.up.railway.app` — DR.12 배포 완료
- **Vercel**: `https://stock-dashboard-alpha-lilac.vercel.app` — 배포 완료

### Changed Files (이번 세션)
**Backend 수정:**
- `backend/api/services/analysis/indicator_signal_service.py` — T+3 필터, RSI 해제, ATR label 개선
- `backend/api/services/analysis/signal_accuracy_service.py` — 해제 신호 제외, min_gap_days 파라미터
- `backend/api/services/analysis/indicator_comparison.py` — start/end_date, min_gap_days 파라미터
- `backend/api/routers/analysis.py` — min_gap_days, start/end_date 파라미터 추가
- `backend/tests/unit/test_indicator_signal_service.py` — frequency 테스트 5건 + RSI 해제 테스트 3건

**Frontend 수정:**
- `frontend/src/pages/IndicatorSignalPage.tsx` — 설명 카드, 해제 배지, 기간 동기화, 성공률 기준 설명
- `frontend/src/components/charts/IndicatorOverlayChart.tsx` — 해제 마커, ATR % 스케일, 참조선
- `frontend/src/api/analysis.ts` — start_date/end_date 파라미터 추가

**Dev docs 생성:**
- `dev/active/phaseD-improve/phaseD-improve-plan.md`
- `dev/active/phaseD-improve/phaseD-improve-context.md`
- `dev/active/phaseD-improve/phaseD-improve-tasks.md`

## Remaining / TODO
- [ ] DI.1~DI.7 커밋 + push
- [ ] 프로덕션 배포 후 브라우저 E2E 확인
- [ ] Phase C 피드백 반영 (post-mvp-feedback.md Phase C 섹션)
- [ ] Phase E 전략 페이지 구현

## Key Decisions
- **T+3 frequency 제어**: 방향 무관 — 마지막 시그널(매수/매도/해제 불문)로부터 3거래일 이후에만 새 시그널
- **RSI 해제 signal 값**: 기존 1/-1/0 체계에 2/-2 추가 (signal_type 필드 대신 단순 확장)
- **ATR % 변환**: 프론트엔드에서 `(atr_14/close)*100`, `vol_20*100` 변환 (백엔드 스키마 변경 불필요)
- **성공률 기간 동기화**: startDate/endDate를 페이지 레벨 상태로 관리, 두 탭 공유

## Context
- 다음 세션에서는 답변에 한국어를 사용하세요.
- **피드백 원본**: `docs/post-mvp-feedback.md` (Phase C/D/E 피드백 모두 포함)
- **Phase D-improve dev-docs**: `dev/active/phaseD-improve/` 참조
- **기존 코드 패턴**: Router-Service-Repository 3계층, 함수형 repo, Pydantic v2, SQLAlchemy 2.0 Mapped
- **Frontend**: React 19 + Vite + TypeScript + Tailwind + axios + react-router-dom v6 + zustand + Recharts
- **SSE 주의**: EventSource(GET) 사용 금지 → fetch + ReadableStream 사용
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
| Phase D-rev 피드백 | ✅ 완료 | 13/13 Tasks |
| Phase D-improve | ✅ 완료 | 7/7 Tasks (추가 개선 Point) |
| Phase E 전략 | ⬜ 미시작 | 9 Steps |
| Phase F~G | ⬜ 미시작 | Memory/Onboarding |

## Next Action
1. DI.1~DI.7 커밋 + push
2. 프로덕션 배포 + 브라우저 E2E 확인
3. Phase C 피드백 반영 또는 Phase E 전략 페이지 구현 (사용자 결정)
