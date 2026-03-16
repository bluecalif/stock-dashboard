# Phase D-rev Debug History
> Last Updated: 2026-03-15

## 알려진 버그 (Phase D에서 발견)

### 정규화 0 스파이크 버그
- **증상**: 지표/가격 오버레이에서 정규화 적용 시 일부 날짜에서 값이 0으로 튀는 포인트 발생
- **원인**: `IndicatorOverlayChart.tsx` `applyTransform()`에서 `?? 0` 사용 — 가격 데이터 없는 날짜의 undefined를 0으로 변환
- **파일**: `frontend/src/components/charts/IndicatorOverlayChart.tsx:119, 124`
- **수정 계획**: DR.8에서 null 필터링으로 해결

## Modified Files Summary
(구현 시작 후 업데이트)

## Lessons Learned
(구현 시작 후 업데이트)
