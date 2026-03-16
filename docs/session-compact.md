# Session Compact

> Generated: 2026-03-16
> Source: Phase D-improve 7/7 완료 + E2E 버그 수정 3건

## Goal
Phase D-improve 완료 후 브라우저 E2E 확인 → 3개 이슈 수정 (시그널 on/off 시각 구분, MACD backfill, 성공률 탭 UI 단순화)

## Completed (Phase D-improve DI.1~DI.7)
- [x] DI.1~DI.7 전체 완료 — `a4e4c16`

## Completed (E2E 버그 수정)
- [x] 차트 시그널 on/off 시각 구분
  - Signal on(1/-1): 실선 strokeWidth=2, 라벨 fontSize 12
  - Signal off(2/-2): 점선 strokeDasharray="2 4", strokeWidth=1, 투명도 0.6
- [x] MACD macd_signal backfill
  - `run_research.py --start 2023-06-01 --end 2025-09-01 --skip-backtest`
  - 7개 자산 69,333 factor rows UPSERT 완료
- [x] 성공률 탭 UI 단순화
  - 예측기간 버튼 제거 → 지표선택 버튼 추가 (시그널 탭과 동일 UI)
  - forwardDays=5 고정, loadAccuracy가 선택된 지표만 조회
  - 요약 패널 "예측 기간: T+N일" 줄 제거

## Current State

### Git 상태
- 최신 커밋: `a4e4c16` (master, DI.1~DI.7 push 완료)
- 미커밋 변경: E2E 버그 수정 3건 (커밋 대기)

### 테스트 상태
- Backend: 26 passed (indicator_signal_service), ruff clean
- Frontend: tsc --noEmit 0 errors

### 인프라 상태
- **Railway**: `https://backend-production-e5bc.up.railway.app`
- **Vercel**: `https://stock-dashboard-alpha-lilac.vercel.app`

### Changed Files (이번 세션 — E2E 수정)
**Frontend 수정:**
- `frontend/src/components/charts/IndicatorOverlayChart.tsx` — 시그널 on/off 시각 구분 (실선/점선)
- `frontend/src/pages/IndicatorSignalPage.tsx` — 성공률 탭 예측기간 제거, 지표선택 추가

**Data 수정:**
- MACD macd_signal backfill (2023-06-01 ~ 2025-09-01, DB UPSERT)

## Remaining / TODO
- [x] DI.1~DI.7 커밋 + push — `a4e4c16`
- [ ] E2E 버그 수정 커밋 + push + 배포
- [ ] 프로덕션 배포 후 브라우저 E2E 재확인
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
1. E2E 버그 수정 커밋 + push + 배포
2. 프로덕션 브라우저 E2E 재확인
3. Phase C 피드백 반영 또는 Phase E 전략 페이지 구현 (사용자 결정)
