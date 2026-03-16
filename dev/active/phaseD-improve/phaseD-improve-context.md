# Phase D-improve: 지표 시그널 추가 개선 — Context
> Last Updated: 2026-03-16
> Status: Step 2부터 시작

## 1. 핵심 파일

### 수정 대상
| 파일 | 용도 | 변경 유형 |
|------|------|-----------|
| `backend/api/services/analysis/indicator_signal_service.py` | on-the-fly 시그널 생성 | T+3 필터, RSI 해제, ATR label |
| `backend/api/services/analysis/signal_accuracy_service.py` | 시그널 성공률 계산 | 해제 신호 제외, min_gap_days 전달 |
| `backend/api/routers/analysis.py` | 분석 REST 엔드포인트 | min_gap_days, start/end_date 파라미터 |
| `backend/api/schemas/analysis.py` | Pydantic 스키마 | signal 값 설명 업데이트 |
| `frontend/src/pages/IndicatorSignalPage.tsx` | 메인 페이지 | 설명 카드, 기간 공유, 해제 배지 |
| `frontend/src/components/charts/IndicatorOverlayChart.tsx` | 오버레이 차트 | 해제 마커, ATR % 스케일 |
| `frontend/src/api/analysis.ts` | API 클라이언트 | 파라미터 추가 |

### 읽기 전용 (참조)
| 파일 | 용도 |
|------|------|
| `backend/api/services/analysis/indicator_analysis.py` | ATR/vol 규칙 (threshold 값) |
| `backend/research_engine/factor_store.py` | LOOKBACK_DAYS=150 |
| `backend/api/services/analysis/indicator_comparison.py` | 지표 비교 서비스 |

## 2. 데이터 인터페이스

### IndicatorSignal (현재)
```python
@dataclass
class IndicatorSignal:
    date: datetime.date
    indicator_id: str       # "rsi_14" | "macd" | "atr_vol"
    signal: int             # 1 (buy), -1 (sell), 0 (warning)
    label: str              # "RSI 과매도 진입" 등
    value: float | None     # 지표값
    entry_price: float | None  # 당일 종가
```

### IndicatorSignal (목표 — Step 3 후)
```python
signal: int  # 1 (buy), -1 (sell), 2 (buy_exit), -2 (sell_exit), 0 (warning)
```

### 시그널 frequency 제어 (Step 2)
```python
def _apply_frequency_filter(
    signals: list[IndicatorSignal],
    min_gap_days: int = 3,
) -> list[IndicatorSignal]:
    """모든 방향 시그널이 min_gap_days 이내이면 제거."""
    filtered = []
    last_date: datetime.date | None = None
    for sig in signals:
        if last_date is not None and (sig.date - last_date).days < min_gap_days:
            continue
        filtered.append(sig)
        last_date = sig.date
    return filtered
```

## 3. API 변경 사항

### /indicator-signals (Step 2)
```
GET /v1/analysis/indicator-signals
  ?asset_id=005930
  &indicator_id=rsi_14
  &start_date=2025-01-01
  &end_date=2026-03-16
  &min_gap_days=3          ← 신규 (기본 3, 0이면 비활성)
```

### /signal-accuracy (Step 5)
```
GET /v1/analysis/signal-accuracy
  ?asset_id=005930
  &indicator_id=rsi_14
  &forward_days=5
  &start_date=2025-01-01   ← 신규
  &end_date=2026-03-16     ← 신규
  &min_gap_days=3           ← 신규
```

### /indicator-comparison (Step 5)
```
GET /v1/analysis/indicator-comparison
  ?asset_id=005930
  &forward_days=5
  &start_date=2025-01-01   ← 신규
  &end_date=2026-03-16     ← 신규
```

## 4. 프론트엔드 설명 텍스트 (Step 1, 6)

### 지표 설명 (시그널 탭)
- RSI: "RSI 14일 — 30 이하 진입 시 매수, 70 이상 진입 시 매도, 복귀 시 해제"
- MACD: "MACD 히스토그램 — 양(+)전환 시 매수, 음(-)전환 시 매도"
- ATR+vol: "ATR/가격 > 3% 또는 변동성 > 30% 시 고변동성 경고"

### 성공률 기준 (성공률 탭)
- "성공 기준: 매수 시그널 후 T+N일 가격 상승, 매도 시 하락"
- "수익률: 각 시그널 T+N일 수익률의 평균"
