# Phase D: 지표 페이지 — Tasks
> Last Updated: 2026-03-13
> Status: 0/11 완료

## Stage A: Backend 분석 서비스
- [ ] D.1 지표 분석 서비스 — 현재 상태 해석 `[M]`
- [ ] D.2 지표 성공률 서비스 ⭐핵심 `[L]`
- [ ] D.3 지표 간 예측력 비교 `[M]`

## Stage B: REST API + LangGraph
- [ ] D.4 분석 REST 엔드포인트 `[M]`
- [ ] D.5 LangGraph Tool — `analyze_indicators` `[M]`
- [ ] D.6 하이브리드 응답 — 지표 카테고리 확장 `[S]`

## Stage C: Frontend 통합 페이지
- [ ] D.7 IndicatorSignalPage 통합 `[L]`
- [ ] D.8 지표 오버레이 차트 `[M]`
- [ ] D.9 성공률 테이블/차트 `[M]`

## Stage D: Frontend 고도화
- [ ] D.10 멀티 지표 설정 + 정규화 `[M]`
- [ ] D.11 chartActionStore 연결 `[S]`

## Stage E: 통합 검증
- [ ] D.12 Phase D 통합 검증 `[M]`
  - Backend: ruff + pytest 전체 통과
  - Frontend: tsc + vite build 성공
  - 프로덕션 배포: git push → Railway/Vercel 배포 확인
  - 프로덕션 브라우저 E2E: 지표 페이지 렌더링, 탭 전환, 오버레이 차트, 성공률 테이블, 챗봇 넛지/하이브리드 응답

## Summary
- **Total**: 12 tasks (S:2, M:7, L:2, XL:1)
- **신규 파일**: ~10
- **수정 파일**: ~7
