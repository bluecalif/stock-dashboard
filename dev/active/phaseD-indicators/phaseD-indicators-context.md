# Phase D: 지표 페이지 — Context
> Last Updated: 2026-03-15
> Status: In Progress (D.2 완료)

## 1. 핵심 파일

### 읽어야 할 기존 코드
| 파일 | 용도 |
|------|------|
| `backend/api/repositories/signal_repo.py` | 시그널 조회 — 성공률 계산에 사용 |
| `backend/api/repositories/price_repo.py` | 가격 조회 — forward return 계산 |
| `backend/api/repositories/factor_repo.py` | 팩터 조회 — 현재 상태 해석 |
| `backend/api/services/llm/tools.py` | 현재 7개 Tool (Phase C 후) — 1개 추가 |
| `backend/api/services/llm/hybrid/classifier.py` | 하이브리드 분류기 — 지표 카테고리 추가 |
| `backend/api/services/llm/hybrid/templates.py` | 응답 템플릿 — 지표 템플릿 추가 |
| `backend/research_engine/factors.py` | 15개 팩터 계산 로직 — 해석 규칙 참고 |
| `frontend/src/pages/FactorPage.tsx` | 기존 팩터 페이지 — 로직 재활용 |
| `frontend/src/pages/SignalPage.tsx` | 기존 시그널 페이지 — 로직 재활용 |
| `frontend/src/store/chartActionStore.ts` | Phase C에서 구축 — 연결 대상 |

## 2. 데이터 인터페이스

### 입력
- `signal_repo.get_signals(db, asset_id, strategy_id, start, end)` → List[SignalDaily]
- `price_repo.get_prices(db, asset_id, start, end)` → List[PriceDaily]
- `factor_repo.get_factors(db, asset_id, factor_name, start, end)` → List[FactorDaily]

### 출력
- REST API JSON 응답 → Frontend 직접 소비
- LangGraph Tool JSON → SSE text_delta
- 분석 결과 DB 저장 없음 (on-the-fly)

## 3. 주요 결정사항

| 결정 | 근거 |
|------|------|
| REST 엔드포인트 추가 | 성공률/비교는 페이지에서 직접 표시 필요 |
| forward_days=5 기본값 | 단기 예측 기준 (일주일) |
| 기존 FactorPage/SignalPage 유지 | 삭제 위험 방지, 라우트만 redirect |
| 탭 UI (3탭) | 지표 현황 + 시그널 + 성공률 자연스러운 분리 |
| 오버레이 차트 별도 YAxis | 가격과 지표 스케일 다름 |
| **지표 확정 (2026-03-15)** | RSI + MACD만 성공률 계산. ATR/vol_20은 경고 전용 |
| **제외 지표** | ROC, vol_zscore_20, ret_*, SMA, EMA — 단독 해석 불가 또는 중복 |
| **macd_signal 신규 추가** | MACD 골든/데드크로스 감지 위해 EMA(9) 필요 → factors.py 수정 |
| **ATR/Price ratio** | DB 저장 없이 API 응답 시 atr_14/close 계산 |
| **고변동성 = sell 경고** | "시장 진입 금지" 수준의 경고 신호. 성공률 계산 제외 |

## Changed Files (Step D.2)
- `backend/api/services/analysis/signal_accuracy_service.py` — 신규 생성
  - `compute_signal_accuracy()`: signal→forward return→성공률 계산
  - `compute_accuracy_all_strategies()`: 복수 전략 일괄 계산 (D.3 재활용)
  - `SignalAccuracyResult`, `SignalDetail` 데이터클래스
  - `MIN_SIGNAL_COUNT = 5` 임계값
- `backend/tests/unit/test_signal_accuracy.py` — 신규 생성 (10 tests)

## 4. 컨벤션 체크리스트

### Backend
- [ ] Router-Service-Repository 3계층 준수
- [ ] Pydantic v2 스키마 (analysis.py)
- [ ] DI 패턴 (db: Session = Depends(get_db))
- [ ] NaN/None 안전 처리 (field_validator)

### Frontend
- [ ] TypeScript strict
- [ ] Recharts ComposedChart 활용
- [ ] 색상코딩: 60%+ 녹색, 40%- 적색
- [ ] 탭 전환 시 상태 유지
