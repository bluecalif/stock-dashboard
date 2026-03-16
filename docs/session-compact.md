# Session Compact

> Generated: 2026-03-16
> Source: Phase D-improve 완료 + E2E 버그 수정 + 추가 색상 수정

## Goal
Phase D-improve 완료. 다음 세션에서 Phase E 전략 페이지 구현 시작.

## Completed (이번 세션)
- [x] DI.1~DI.7 전체 완료 — `a4e4c16`
- [x] E2E 버그 수정 3건 — `19daaa9`
  - 시그널 on/off 시각 구분, MACD backfill, 성공률 탭 UI 단순화
- [x] 추가 색상 수정 — `b359598`
  - 시그널 on/off 구분 강화 (entry 굵게, exit 투명도 0.35)
  - 매도해제 색상 orange → gray
  - 바 차트: 매수=초록, 매도=빨강 고정
  - 비교 테이블/요약: 매수=초록계열, 매도=빨강계열

## Known Issues (다음 revisit)
- 성공률 탭 색상 규칙이 프로덕션에서 미반영 — API 응답 또는 컴포넌트 핸들링 이슈 가능성

## Current State

### Git 상태
- 최신 커밋: `b359598` (master, push 완료)
- 미커밋 변경: 없음

### 테스트 상태
- Backend: 26 passed (indicator_signal_service), ruff clean
- Frontend: tsc --noEmit 0 errors

### 인프라 상태
- **Railway**: `https://backend-production-e5bc.up.railway.app`
- **Vercel**: `https://stock-dashboard-alpha-lilac.vercel.app`

## Key Decisions
- **T+3 frequency 제어**: 방향 무관 — 마지막 시그널로부터 3거래일 이후에만 새 시그널
- **RSI 해제 signal 값**: 기존 1/-1/0 체계에 2/-2 추가
- **ATR % 변환**: 프론트엔드에서 `(atr_14/close)*100`, `vol_20*100` 변환
- **성공률 기간 동기화**: startDate/endDate 페이지 레벨 상태, 두 탭 공유
- **색상 규칙**: 매수=초록, 매도=빨강 고정 (값 기반 색상 제거)

## Context
- 다음 세션에서는 답변에 한국어를 사용하세요.
- **피드백 원본**: `docs/post-mvp-feedback.md` (Phase C/D/E 피드백 모두 포함)
- **Phase E dev-docs**: `dev/active/phaseE-strategy/` 참조
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
| Phase D-improve | ✅ 완료 | 7/7 Tasks + E2E 수정 |
| Phase E 전략 | 🔄 진행중 | 4/10 완료 (E.1~E.4) |
| Phase F~G | ⬜ 미시작 | Memory/Onboarding |

## Next Action
1. E.4 전략 백테스트 REST 엔드포인트
2. E.5 LangGraph Tool + 하이브리드 전략 확장
3. 성공률 탭 색상 이슈 revisit
