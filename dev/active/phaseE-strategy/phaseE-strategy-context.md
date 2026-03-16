# Phase E: 전략 페이지 — Context
> Last Updated: 2026-03-16
> Status: In Progress (E.5 완료, Stage A+B 완료)

## 1. 핵심 파일

### 읽어야 할 기존 코드
| 파일 | 용도 |
|------|------|
| `backend/api/services/analysis/indicator_signal_service.py` | Phase D-rev 핵심 — RSI/MACD/ATR+vol on-the-fly 시그널 생성 |
| `backend/research_engine/backtest.py` | 백테스트 엔진 — run_backtest(), TradeRecord, BacktestResult |
| `backend/research_engine/metrics.py` | 성과 지표 — compute_metrics(), PerformanceMetrics |
| `backend/research_engine/strategies/` | 기존 3종 전략 (하위호환 참고용) |
| `backend/api/services/backtest_service.py` | 기존 백테스트 서비스 — 참고용 |
| `backend/api/routers/analysis_router.py` | Phase D에서 생성 — POST 추가 |
| `backend/api/schemas/analysis.py` | Phase D에서 생성 — 스키마 추가 |
| `backend/api/services/llm/tools.py` | 현재 Tool 목록 — 1개 추가 |
| `backend/api/services/llm/hybrid/` | Phase C에서 구축 — 전략 카테고리 추가 |
| `frontend/src/pages/StrategyPage.tsx` | 기존 전략 페이지 — 전면 개편 대상 |
| `frontend/src/components/charts/EquityCurveChart.tsx` | 에쿼티 커브 — 이벤트 마커 확장 기반 |

### 전략-지표 매핑 (피드백 기반 재정의)
| 전략명 | strategy_name | indicator_id | indicator_signal_service 함수 |
|--------|--------------|-------------|------------------------------|
| 모멘텀 | momentum | macd | `generate_indicator_signals(db, asset_id, "macd", ...)` |
| 역발상 | contrarian | rsi_14 | `generate_indicator_signals(db, asset_id, "rsi_14", ...)` |
| 위험회피 | risk_aversion | atr_vol | `generate_indicator_signals(db, asset_id, "atr_vol", ...)` |

## 2. 데이터 인터페이스

### 입력
- `indicator_signal_service.generate_indicator_signals(db, asset_id, indicator_id, start, end, min_gap_days)` → DataFrame [date, signal, value, description]
- `backtest.run_backtest(prices_df, signals_df, asset_id, strategy_id, config)` → BacktestResult
- `metrics.compute_metrics(result)` → PerformanceMetrics
- `price_repo.get_prices()` — 가격 데이터

### 출력
- REST API JSON → Frontend StrategyPage
- LangGraph Tool JSON → SSE text_delta
- on-the-fly 결과 (DB 저장 없음)

### 응답 구조 (StrategyBacktestResponse)
```python
{
    "asset_id": "005930",
    "strategy_name": "momentum",
    "strategy_label": "모멘텀 (MACD)",
    "period": "2Y",
    "initial_cash": 100_000_000,
    "metrics": { ... },                    # PerformanceMetrics
    "equity_curve": [ ... ],                # [{date, equity, drawdown, bh_equity}]
    "trades": [ ... ],                      # [{entry_date, exit_date, pnl, narrative, is_best, is_worst}]
    "annual_performance": [ ... ],          # [{year, return_pct, pnl_amount, is_favorable}]
    "summary_narrative": "모멘텀 전략은...",   # 전체 요약 텍스트
    "best_trade": { ... },                  # Best 거래 상세
    "worst_trade": { ... },                 # Worst 거래 상세
    "loss_avoided": 5_230_000               # 위험회피 전략 전용: B&H 대비 손실 회피 금액
}
```

## 3. 주요 결정사항

| 결정 | 근거 |
|------|------|
| indicator 시그널 기반 전략으로 전환 | 피드백: MACD=모멘텀, RSI=역발상, ATR+vol=위험회피. Phase D-rev indicator_signal_service 활용 |
| on-the-fly 백테스트 (DB 미저장) | DB에 없는 기간 조합도 즉시 실행 |
| initial_cash=100,000,000 (1억원) | 한국 투자자 기준 직관적 금액 |
| 1년 단위 성과 분석 | 피드백: 전략이 잘 맞는 구간인지 아닌지 연도별 표현 |
| Best/Worst 거래 visual annotation | 피드백: 효과 큰 구간 + 실패 구간 그래프 내 설명 삽입 |
| 위험회피 손실 회피 금액 = max(0, bh_equity - strategy_equity) 누적 | 탈출 구간에서 B&H 대비 절감된 손실 |
| 스토리텔링 하드코딩 템플릿 | 추상 점수 금지, 실제 금액/수익률만 |
| 기존 research_engine strategies 하위호환 유지 | 기존 백테스트 API 영향 없음 |
| 기존 FactorPage/SignalPage 삭제 안 함 | 안전, 라우트만 redirect |

## Changed Files (Step E.1)
- `backend/api/services/analysis/strategy_backtest_service.py` — 신규 생성
- `backend/tests/unit/test_strategy_backtest_service.py` — 신규 생성 (20 tests)

## Changed Files (Step E.2)
- `backend/api/services/analysis/annual_performance_service.py` — 신규 생성
- `backend/tests/unit/test_annual_performance.py` — 신규 생성 (12 tests)

## Changed Files (Step E.3)
- `backend/api/services/analysis/storytelling_service.py` — 신규 생성
- `backend/tests/unit/test_storytelling.py` — 신규 생성 (19 tests)

## Changed Files (Step E.4)
- `backend/api/routers/analysis.py` — POST /v1/analysis/strategy-backtest 추가
- `backend/api/schemas/analysis.py` — StrategyBacktestRequest/Response 스키마 추가

## 4. 컨벤션 체크리스트

### Backend
- [x] indicator_signal_service 시그널 → backtest.run_backtest() 입력 변환
- [ ] 금액 포맷: 원화 (₩) + 천 단위 쉼표 (프론트에서 처리)
- [ ] 수익률: 소수점 2자리 (%)
- [ ] NaN/None 안전 처리
- [x] 위험회피 전략: loss_avoided 계산 로직 검증
- [ ] 연간 성과: 6개월 미만 데이터 연도 제외 또는 부분연도 라벨

### Frontend
- [ ] ReferenceDot: 매수=초록, 매도=빨강
- [ ] Best 구간: 초록 하이라이트 ReferenceArea + 수익 금액 라벨
- [ ] Worst 구간: 빨강 하이라이트 ReferenceArea + 손실 금액 라벨
- [ ] 내러티브 카드: 클릭 이벤트 → 패널 표시
- [ ] 연간 바 차트: 적합=초록, 부적합=빨강
- [ ] 기간 프리셋: 6M/1Y/2Y/3Y 버튼
- [ ] 금액 포맷: toLocaleString('ko-KR') + ₩
- [ ] 위험회피: 손실 회피 금액 별도 카드 또는 라벨
