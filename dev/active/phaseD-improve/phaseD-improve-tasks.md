# Phase D-improve: 지표 시그널 추가 개선 — Tasks
> Last Updated: 2026-03-16
> Status: 7/7 (100%)

## Stage A: Backend — 시그널 로직 개선
- [x] DI.1 지표 설명 및 판정 기준 표시 (프론트엔드) `[S]`
- [x] DI.2 T+3 시그널 frequency 제어 (백엔드) `[M]`
  - `_apply_frequency_filter()` 추가, 방향 무관 gap 필터
  - API `min_gap_days` 파라미터 추가 (기본 3, 0=비활성)
  - 테스트 5건 추가
- [x] DI.3 RSI 해제 신호 추가 (백엔드 + 프론트엔드) `[M]`
  - `signal=2` (매수해제), `signal=-2` (매도해제) 확장
  - 성공률 계산에서 `signal in (1, -1)`만 평가
  - 프론트: 해제 배지(파란/주황) + 차트 "X" 마커
  - 테스트 3건 추가

## Stage B: Frontend — ATR + 성공률 개선
- [x] DI.4 ATR+변동성 스케일 개선 (백엔드 + 프론트엔드) `[M]`
  - ATR → (atr_14/close)*100 %, vol_20 → *100 % 변환
  - 참조선: ATR 3%, 변동성 30%
  - 백엔드 label에 트리거 지표 명시
- [x] DI.5 성공률 탭 기간 동기화 (백엔드 + 프론트엔드) `[M]`
  - `/signal-accuracy`, `/indicator-comparison`에 start_date/end_date 파라미터 추가
  - `compare_indicators()`에 기간 + min_gap_days 전달
  - 프론트: DateRangePicker 공유, API 호출 시 기간 전달
- [x] DI.6 성공률 데이터 매칭 + 기준 설명 (프론트엔드) `[S]`
  - "예측 기간: T+N일", "성공 기준: 매수→상승, 매도→하락" 설명 카드

## Stage C: 검증
- [x] DI.7 MACD signal lookback 검증 `[S]`
  - DR.12 LOOKBACK_DAYS=150 확장으로 해결 확인, 추가 변경 불필요
