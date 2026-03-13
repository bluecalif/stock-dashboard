# Phase E: 전략 페이지 — Context
> Last Updated: 2026-03-13
> Status: Planning

## 1. 핵심 파일

### 읽어야 할 기존 코드
| 파일 | 용도 |
|------|------|
| `backend/research_engine/backtest.py` | 백테스트 엔진 — on-the-fly 실행 |
| `backend/research_engine/metrics.py` | 성과 지표 — compute_metrics() |
| `backend/research_engine/strategies/` | 3종 전략 (momentum, trend, mean_reversion) |
| `backend/api/services/backtest_service.py` | 기존 백테스트 서비스 — 참고용 |
| `backend/api/routers/analysis_router.py` | Phase D에서 생성 — POST 추가 |
| `backend/api/schemas/analysis.py` | Phase D에서 생성 — 스키마 추가 |
| `backend/api/services/llm/tools.py` | 현재 8개 Tool (Phase D 후) — 1개 추가 |
| `backend/api/services/llm/hybrid/` | Phase C에서 구축 — 전략 카테고리 추가 |
| `frontend/src/pages/StrategyPage.tsx` | 기존 전략 페이지 — 확장 대상 |
| `frontend/src/components/charts/EquityCurveChart.tsx` | 에쿼티 커브 — 이벤트 마커 확장 기반 |

## 2. 데이터 인터페이스

### 입력
- `research_engine/backtest.run_backtest(prices_df, signals_df, ...)` → BacktestResult
- `research_engine/metrics.compute_metrics(equity_curve)` → MetricsResult
- `price_repo.get_prices()`, `signal_repo.get_signals()` — 데이터 조회

### 출력
- REST API JSON → Frontend StrategyPage
- LangGraph Tool JSON → SSE text_delta
- on-the-fly 결과 (DB 저장 없음)

## 3. 주요 결정사항

| 결정 | 근거 |
|------|------|
| on-the-fly 백테스트 (DB 미저장) | DB에 없는 기간 조합도 즉시 비교 |
| initial_cash=100,000,000 (1억원) | 한국 투자자 기준 직관적 금액 |
| 스토리텔링 하드코딩 템플릿 | 추상 점수 금지, 실제 금액/수익률만 |
| 내러티브 규칙별 표현 분기 | 수익/손실, 장기(>60일), 대폭(>10%) |
| 기존 FactorPage/SignalPage 삭제 안 함 | 안전, 라우트만 redirect |

## 4. 컨벤션 체크리스트

### Backend
- [ ] on-the-fly 백테스트: research_engine 직접 호출
- [ ] 금액 포맷: 원화 (₩) + 천 단위 쉼표
- [ ] 수익률: 소수점 2자리 (%)
- [ ] NaN/None 안전 처리

### Frontend
- [ ] ReferenceDot: 매수=파란, 매도=빨간
- [ ] 내러티브 카드: 클릭 이벤트 → 패널 표시
- [ ] 기간 프리셋: 6M/1Y/2Y 버튼
- [ ] 금액 포맷: toLocaleString('ko-KR')
