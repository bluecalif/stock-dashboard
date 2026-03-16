# Phase D-rev: 지표 페이지 피드백 반영 — Tasks
> Last Updated: 2026-03-15
> Status: 11/13 (85%)

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

## Stage E: 추가 피드백 수정
- [x] DR.11 오버레이 지표 표시 + MACD 시그널라인 `[M]` — `92f964d`
  - IndicatorSignalPage에서 factor 시계열 fetch → 차트에 지표 곡선 오버레이
  - INDICATOR_FACTOR_MAP: rsi_14, macd+macd_signal, atr_14+vol_20
  - 시그널 이력 패널에 지표값(sig.value) 수치 표시
- [x] DR.11b repo 쿼리 정렬 DESC→ASC 수정 `[S]` — `4301224`
  - price_repo, factor_repo, signal_repo: date DESC → ASC
  - limit=500 + DESC 조합에서 최신 데이터만 반환되던 버그 수정

## Stage F: 팩터 데이터 파이프라인 수정
- [ ] DR.12 팩터 계산 lookback 확장 `[M]`
  - `factor_store.py`의 `store_factors_for_asset()` — preprocess 시 start를 150일 앞당겨 lookback 확보
  - 팩터 계산 후 원래 요청 범위만 DB에 저장 (trim)
  - 근본 원인: daily-collect.yml이 T-7~T 범위만 전달 → 7일 가격으로 RSI(14)/ATR(14)/vol(20)/SMA(120) 계산 불가
- [ ] DR.13 프로덕션 백필 + 통합 검증 `[M]`
  - DR.12 배포 후 workflow_dispatch로 백필 (start: 2025-10-01, end: 2026-03-15)
  - 프로덕션 API로 팩터 데이터 갭 복구 확인
  - 브라우저 E2E: 오버레이 차트에서 RSI/MACD+시그널/ATR 전체 기간 표시 확인

## Summary
- **Total**: 13 tasks (S:3, M:7, L:2)
- **완료**: 11/13 (85%)
- **남은 작업**: DR.12 (팩터 lookback), DR.13 (백필 + 검증)
