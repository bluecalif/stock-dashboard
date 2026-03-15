# Phase D-rev: 지표 페이지 피드백 반영 — Tasks
> Last Updated: 2026-03-15
> Status: 0/10 (0%)

## Stage A: Backend — 지표별 시그널 생성
- [x] DR.1 지표별 시그널 생성 서비스 (indicator_signal_service.py 신규) `[L]`
- [x] DR.2 지표별 성공률 계산 수정 (signal_accuracy_service.py 확장) `[M]`

## Stage B: Backend — API + 비교 수정
- [x] DR.3 지표 비교 서비스 수정 (RSI vs MACD) `[M]`
- [x] DR.4 API 엔드포인트 수정 + 신규 (indicator-signals) `[M]`

## Stage C: Frontend — 탭 통합 + 레이아웃
- [x] DR.5 3탭→2탭 전환 + 전략 배제 (IndicatorSignalPage 전면 수정) `[L]`
- [x] DR.6 시그널 탭 레이아웃 (차트 3/4 + 설명 1/4, 수직 점선) `[M]`
- [x] DR.7 성공률 탭 레이아웃 (차트 3/4 + 거래 테이블 1/4) `[M]`

## Stage D: Frontend — 버그 수정 + 특수 처리
- [x] DR.8 정규화 버그 수정 (IndicatorOverlayChart null 처리) `[S]`
- [x] DR.9 ATR(+vol) 특수 처리 (위험 구간 + 성공률 분리) `[S]`

## Stage E: 통합 검증
- [ ] DR.10 Phase D-rev 통합 검증 `[M]`

## Summary
- **Total**: 10 tasks (S:2, M:5, L:2)
- **완료**: 9/10 (90%)
- **신규 파일**: ~2 (Backend)
- **수정 파일**: ~11 (Backend 5 + Frontend 6)
