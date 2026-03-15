# Phase D-rev: 지표 페이지 피드백 반영 — Context
> Last Updated: 2026-03-15
> Status: Planning

## 1. 핵심 파일

### 읽어야 할 기존 코드
| 파일 | 용도 | 변경 유형 |
|------|------|-----------|
| `backend/api/services/analysis/indicator_analysis.py` | RSI/MACD/ATR/vol_20 해석 규칙 — **시그널 생성 로직의 기반** | 읽기 전용 (규칙 재활용) |
| `backend/api/services/analysis/signal_accuracy_service.py` | 현재 strategy 기반 성공률 계산 | 수정 (indicator_id 지원 추가) |
| `backend/api/services/analysis/indicator_comparison.py` | 현재 3전략 비교 | 수정 (RSI vs MACD 비교) |
| `backend/api/routers/analysis.py` | 분석 REST 엔드포인트 | 수정 (새 엔드포인트 + 파라미터) |
| `backend/api/schemas/analysis.py` | Pydantic 요청/응답 | 수정 (신규 스키마) |
| `backend/api/repositories/factor_repo.py` | 팩터 시계열 조회 | 읽기 전용 |
| `backend/api/repositories/price_repo.py` | 종가 조회 | 읽기 전용 |
| `backend/research_engine/factors.py` | 15개 팩터 계산 (macd_signal 포함) | 읽기 전용 |
| `frontend/src/pages/IndicatorSignalPage.tsx` | 3탭 통합 페이지 — **전면 수정 대상** | 대규모 수정 |
| `frontend/src/components/charts/IndicatorOverlayChart.tsx` | 가격+지표 오버레이 — **정규화 버그 수정** | 수정 |
| `frontend/src/components/charts/AccuracyBarChart.tsx` | 성공률 막대 차트 | 수정 (지표별 전환) |
| `frontend/src/api/analysis.ts` | API 클라이언트 | 수정 (새 API 함수) |
| `frontend/src/types/api.ts` | 타입 정의 | 수정 (신규 타입) |

### 신규 파일
| 파일 | 용도 |
|------|------|
| `backend/api/services/analysis/indicator_signal_service.py` | **핵심** — 지표별 on-the-fly 시그널 생성 |
| `backend/tests/unit/test_indicator_signal_service.py` | 시그널 생성 테스트 |

## 2. 데이터 인터페이스

### 입력 (기존 — 변경 없음)
- `factor_repo.get_factors(db, asset_id, factor_name, start, end)` → List[FactorDaily]
- `price_repo.get_prices(db, asset_id, start, end)` → List[PriceDaily]

### 출력 (변경)
- **신규 REST**: `GET /v1/analysis/indicator-signals?asset_id=&indicator_id=&start_date=&end_date=`
  ```json
  {
    "asset_id": "005930",
    "indicator_id": "rsi_14",
    "signals": [
      {"date": "2025-06-15", "signal": 1, "label": "RSI 과매도 진입", "value": 28.5, "entry_price": 72000},
      {"date": "2025-07-20", "signal": -1, "label": "RSI 과매수 진입", "value": 73.2, "entry_price": 81000}
    ],
    "total_signals": 2
  }
  ```
- **수정 REST**: `GET /v1/analysis/signal-accuracy?asset_id=&indicator_id=rsi_14&forward_days=5`
  - `indicator_id`와 `strategy_id` 중 하나 필수 (둘 다 없으면 422)
  - 응답 구조 동일 (SignalAccuracyResponse)
- **수정 REST**: `GET /v1/analysis/indicator-comparison?asset_id=&forward_days=5`
  - 기존: 3전략 비교 → 변경: RSI vs MACD 비교
  - 응답: `strategies` → `indicators` 키명 변경

## 3. 주요 결정사항

| 결정 | 근거 |
|------|------|
| **on-the-fly 시그널 생성** (DB 저장 안 함) | 시그널이 factor_daily에서 파생 가능. 신규 테이블 불필요 |
| **전환점(transition) 감지 방식** | 단순 임계값이 아닌, 이전일→당일 교차 여부로 판단 → 시그널 과다 방지 |
| **기존 strategy 기반 API 하위호환** | Phase E 전략 페이지에서 사용. strategy_id 파라미터 유지 |
| **ATR+vol 통합 처리** | ATR/Price ratio + vol_20을 하나의 "위험도" 지표로 묶어 표시 |
| **성공률 계산 대상: RSI, MACD만** | ATR은 방향 시그널 아님 → 성공률 산출 불가 (기존 결정 유지) |
| **시그널 수직 점선** | Recharts `ReferenceLine` x={date} + strokeDasharray |
| **3/4 + 1/4 레이아웃** | Tailwind `grid grid-cols-4` → 차트 `col-span-3` + 패널 `col-span-1` |

### RSI 시그널 전환점 기준
| 조건 | signal | label |
|------|--------|-------|
| 이전 RSI ≥ 30 → 당일 RSI < 30 | buy (+1) | RSI 과매도 진입 |
| 이전 RSI ≤ 70 → 당일 RSI > 70 | sell (-1) | RSI 과매수 진입 |
| 이전 RSI < 20 → 당일 RSI ≥ 20 | neutral (0) | RSI 극단적 과매도 이탈 (참고용) |

### MACD 시그널 전환점 기준
| 조건 | signal | label |
|------|--------|-------|
| 이전 histogram ≤ 0 → 당일 > 0 | buy (+1) | MACD 골든크로스 |
| 이전 histogram ≥ 0 → 당일 < 0 | sell (-1) | MACD 데드크로스 |

### ATR+vol 위험 구간 기준
| 조건 | signal | label |
|------|--------|-------|
| ATR/Price > 3% 또는 vol_20 > 0.3 | warning (0) | 고변동성 경고 구간 진입 |
| ATR/Price ≤ 3% 그리고 vol_20 ≤ 0.3 | - | 정상 구간 복귀 |

## 4. 정규화 버그 상세

**현재 코드** (`IndicatorOverlayChart.tsx:119, 124`):
```typescript
const priceValues = raw.map((p) => (p.close as number) ?? 0);  // BUG: null → 0
const vals = raw.map((p) => (p[f] as number) ?? 0);              // BUG: null → 0
```

**문제**: 가격 데이터가 없는 날짜(공휴일 등)에서 `close`가 undefined → 0으로 변환됨 → 정규화 시 그래프가 0으로 급락하는 스파이크 발생

**수정 방안**:
1. `mergeRawData()`에서 가격 없는 날짜의 포인트를 아예 제외하거나
2. `applyTransform()`에서 `null`/`undefined` 값을 건너뛰고 보간
3. Recharts `connectNulls` prop으로 null 구간 연결 (이미 적용 중이나 0은 null이 아니라 무효)

**선택: 방안 1** — 가격이 없는 날짜는 차트에서 제외 (가장 안전)

## 5. 컨벤션 체크리스트

### Backend
- [ ] Router-Service-Repository 3계층 준수
- [ ] Pydantic v2 스키마 (analysis.py 확장)
- [ ] DI 패턴 (db: Session = Depends(get_db))
- [ ] NaN/None 안전 처리 (field_validator)
- [ ] 기존 strategy_id 기반 API 하위호환 유지

### Frontend
- [ ] TypeScript strict
- [ ] Recharts ReferenceLine (수직 점선)
- [ ] grid grid-cols-4 레이아웃 (3/4 + 1/4)
- [ ] 색상코딩: 성공=녹색, 실패=적색
- [ ] 정규화 시 null 안전 처리
