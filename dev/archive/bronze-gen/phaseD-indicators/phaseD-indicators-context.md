# Phase D: 지표 페이지 — Context
> Last Updated: 2026-03-15
> Status: In Progress (D.11 완료, D.12 남음)

## 1. 핵심 파일

### 읽어야 할 기존 코드
| 파일 | 용도 |
|------|------|
| `backend/api/repositories/signal_repo.py` | 시그널 조회 — 성공률 계산에 사용 |
| `backend/api/repositories/price_repo.py` | 가격 조회 — forward return 계산 |
| `backend/api/repositories/factor_repo.py` | 팩터 조회 — 현재 상태 해석 |
| `backend/api/services/llm/tools.py` | 현재 8개 Tool (analyze_indicators 추가) |
| `backend/api/services/llm/hybrid/classifier.py` | 하이브리드 분류기 — 지표 카테고리 9개 |
| `backend/api/services/llm/hybrid/templates.py` | 응답 템플릿 — 지표 템플릿 3개 |
| `backend/research_engine/factors.py` | 15개 팩터 계산 로직 — 해석 규칙 참고 |
| `frontend/src/pages/IndicatorSignalPage.tsx` | 3탭 통합 페이지 (D.7~D.11) |
| `frontend/src/store/chartActionStore.ts` | Phase C에서 구축 — D.11에서 연결 완료 |

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
| **정규화 3모드** | 원본/min-max(0~100)/% 변화 — 스케일 다른 지표 비교용 |
| **MACD 오버레이 제외** | 히스토그램 차트가 별도로 더 적합, 오버레이에서는 자동 제외 |

## Changed Files (Step D.3~D.6) — 커밋 완료
- `backend/api/services/analysis/indicator_comparison.py` — 신규 (D.3)
- `backend/api/schemas/analysis.py` — 신규 (D.4)
- `backend/api/routers/analysis.py` — 신규 (D.4)
- `backend/api/main.py` — 수정 (analysis 라우터 등록)
- `backend/api/services/llm/tools.py` — 수정 (analyze_indicators 도구 추가)
- `backend/api/services/llm/hybrid/classifier.py` — 수정 (지표 패턴 9개)
- `backend/api/services/llm/hybrid/templates.py` — 수정 (지표 템플릿 3개)
- `backend/api/services/chat/chat_service.py` — 수정 (_fetch_hybrid_data 지표 분기)
- `backend/tests/unit/test_indicator_comparison.py` — 신규 (9 tests)
- `backend/tests/unit/test_api/test_analysis_router.py` — 신규 (7 tests)
- `backend/tests/unit/test_hybrid_classifier.py` — 수정 (+19 tests)

## Changed Files (Step D.7~D.11) — 미커밋
- `frontend/src/pages/IndicatorSignalPage.tsx` — 신규 (D.7, 3탭 통합)
- `frontend/src/api/analysis.ts` — 신규 (성공률/비교 API 클라이언트)
- `frontend/src/types/api.ts` — 수정 (분석 응답 타입 추가)
- `frontend/src/App.tsx` — 수정 (/indicators 라우트, /factors·/signals redirect)
- `frontend/src/components/layout/Sidebar.tsx` — 수정 (팩터+시그널 → 지표/시그널 통합)
- `frontend/src/components/charts/IndicatorOverlayChart.tsx` — 신규 (D.8, 가격+지표 오버레이)
- `frontend/src/components/charts/AccuracyBarChart.tsx` — 신규 (D.9, 성공률 막대 차트)
- `frontend/src/components/common/IndicatorSettingsPanel.tsx` — 신규 (D.10, 오버레이 설정)

## 4. 컨벤션 체크리스트

### Backend
- [x] Router-Service-Repository 3계층 준수
- [x] Pydantic v2 스키마 (analysis.py)
- [x] DI 패턴 (db: Session = Depends(get_db))
- [x] NaN/None 안전 처리 (field_validator)

### Frontend
- [x] TypeScript strict
- [x] Recharts ComposedChart 활용
- [x] 색상코딩: 60%+ 녹색, 40%- 적색
- [x] 탭 전환 시 상태 유지
