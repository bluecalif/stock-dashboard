# Phase E: 전략 페이지 — Tasks
> Last Updated: 2026-03-16
> Status: 3/10 완료 (30%)

## Stage A: Backend 전략 백테스트 서비스
- [x] E.1 전략 백테스트 서비스 (indicator 시그널 → on-the-fly 백테스트) `[L]`
- [x] E.2 연간 성과 분석 서비스 (1년 단위 슬라이싱 + 적합도) `[M]`
- [x] E.3 이벤트 스토리텔링 서비스 (Best/Worst 식별 + 내러티브) `[L]`

## Stage B: REST + LangGraph
- [ ] E.4 전략 백테스트 REST 엔드포인트 `[M]`
- [ ] E.5 LangGraph Tool + 하이브리드 전략 확장 `[M]`

## Stage C: Frontend
- [ ] E.6 전략 사전 설명 카드 (모멘텀/역발상/위험회피) `[S]`
- [ ] E.7 에쿼티 커브 이벤트 마커 + Best/Worst annotation + 내러티브 ⭐핵심 `[XL]`
- [ ] E.8 연간 성과 차트 + 기간 설정 + 1억원 시드 `[L]`
- [ ] E.9 라우트 최종 정리 `[S]`

## Stage D: 통합 검증
- [ ] E.10 Phase E 통합 검증 `[M]`
  - Backend: ruff + pytest 전체 통과
  - Frontend: tsc + vite build 성공
  - 프로덕션 배포: git push → Railway/Vercel 배포 확인
  - 프로덕션 브라우저 E2E: 전략 페이지 렌더링, 설명 카드, 매매 마커, Best/Worst annotation, 내러티브 패널, 연간 성과, 기간 설정, 위험회피 손실 회피, 라우트 정리, 챗봇 연동

## Summary
- **Total**: 10 tasks (S:2, M:3, L:3, XL:1)
- **신규 파일**: ~8
- **수정 파일**: ~8
