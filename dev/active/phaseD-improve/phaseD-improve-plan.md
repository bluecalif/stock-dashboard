# Phase D-improve: 지표 시그널 추가 개선
> Last Updated: 2026-03-16
> Status: Planning
> Source: `docs/post-mvp-feedback.md` 추가 개선 Point 섹션

## 1. Summary (개요)

**목적**: Phase D-rev 완료 후 추가 피드백 반영 — 시그널 빈도 제어, RSI 해제 신호, ATR 스케일 개선, 성공률 기간 동기화
**범위**: 백엔드 시그널 생성 로직 개선 + 프론트엔드 UX 보강
**원칙**: 기존 D-rev 코드 위에 증분 개선, 기존 API 하위호환 유지

## 2. Current State (현재 상태)

- **Phase D-rev 13/13 완료** (`d942cfc` — 2026-03-15)
- 2탭 (시그널/성공률) 구조 완성
- 지표별(RSI/MACD/ATR+vol) on-the-fly 시그널 생성
- LOOKBACK_DAYS=150 확장 완료
- 테스트: 681 passed, 7 skipped, ruff clean
- Frontend: tsc --noEmit 0 errors, vite build 성공

## 3. Target State (목표 상태)

| 항목 | 현재 | 목표 |
|------|------|------|
| 시그널 빈도 | 모든 crossover 감지 | **T+3 frequency 제어** (방향 무관) |
| RSI 신호 | 진입만 (매수/매도) | **진입 + 해제** (매수해제/매도해제) |
| ATR 스케일 | atr_pct(0.01~0.05) + vol(0.1~0.5) 혼재 | **% 통일 + 참조선** |
| 성공률 기간 | 전체 기간 고정 | **시그널 탭과 동기화** |
| 판정 기준 | 표시 없음 | **지표별 설명 카드** |

## 4. Steps

### Step 1: 지표 설명 및 판정 기준 표시 (프론트엔드)
시그널 탭에서 지표 선택 시 해당 지표의 판정 기준을 간결하게 표시.

**변경 파일**:
- `frontend/src/pages/IndicatorSignalPage.tsx`

**상세**:
- `INDICATOR_DESCRIPTIONS` 상수 추가
  - RSI: "RSI 14일 — 과매수(>70)/과매도(<30) 교차 시 매도/매수 신호"
  - MACD: "MACD 히스토그램 — 골든크로스(+전환)/데드크로스(-전환) 기반"
  - ATR+vol: "ATR/가격비율(>3%) + 변동성(>30%) — 고변동성 경고"
- 시그널 이력 패널 상단에 설명 카드 렌더링

---

### Step 2: T+3 시그널 frequency 제어 (백엔드)
**모든 방향** 시그널이 3거래일 이내 반복 시 후자 제거.
방향 무관 — 마지막 시그널 발생일로부터 T+3일 이후에만 새 시그널 카운트.

**변경 파일**:
- `backend/api/services/analysis/indicator_signal_service.py`
- `backend/api/routers/analysis.py`

**상세**:
- `_apply_frequency_filter(signals, min_gap_days=3)` 후처리 함수 추가
  - `last_signal_date` 단일 변수 (방향 무관)
  - `(sig.date - last_signal_date).days < min_gap_days` → skip
- `generate_indicator_signals()`에 `min_gap_days` 파라미터 추가, 반환 전 필터 적용
- API 엔드포인트에 `min_gap_days: int = Query(default=3, ge=0)` 추가
- 성공률 서비스도 동일 파라미터 전달

---

### Step 3: RSI 해제 신호 (백엔드 + 프론트엔드)
RSI 70 아래 복귀 → "매도 해제", RSI 30 위 복귀 → "매수 해제".

**변경 파일**:
- `backend/api/services/analysis/indicator_signal_service.py`
- `backend/api/services/analysis/signal_accuracy_service.py`
- `backend/api/schemas/analysis.py`
- `frontend/src/pages/IndicatorSignalPage.tsx`
- `frontend/src/components/charts/IndicatorOverlayChart.tsx`

**상세**:
- `_generate_rsi_signals()`: `signal=2` (매수해제=과매도 탈출), `signal=-2` (매도해제=과매수 탈출)
- 성공률 계산에서 `abs(signal) != 1` → skip
- 프론트엔드: "해제" 배지 (파란/주황), 마커 "X" 표시

---

### Step 4: ATR+변동성 스케일 개선 (백엔드 + 프론트엔드)
ATR과 변동성 각각의 시그널 기준 명확화 + 스케일 % 통일.

**변경 파일**:
- `backend/api/services/analysis/indicator_signal_service.py`
- `frontend/src/components/charts/IndicatorOverlayChart.tsx`

**상세**:
- 백엔드: label에 트리거 지표 명시 ("ATR 3% 초과" / "변동성 30% 초과")
- 프론트엔드: atr_14를 `(atr_14/close)*100`으로 % 변환, vol_20도 `*100` % 변환
- 참조선: ATR 3%, 변동성 30% 수평선 (ReferenceLine)

---

### Step 5: 성공률 탭 기간 동기화 (백엔드 + 프론트엔드)
시그널 탭과 성공률 탭이 동일한 startDate/endDate 공유.

**변경 파일**:
- `backend/api/routers/analysis.py`
- `backend/api/services/analysis/indicator_comparison.py`
- `frontend/src/pages/IndicatorSignalPage.tsx`
- `frontend/src/api/analysis.ts`

**상세**:
- 백엔드: `/signal-accuracy`, `/indicator-comparison`에 `start_date`, `end_date` 파라미터 추가
- 프론트엔드: startDate/endDate 상태를 페이지 레벨에서 관리, 두 탭 공유

---

### Step 6: 성공률 데이터 매칭 + 기준 설명 (프론트엔드)
지표별 요약 카드에 성공률/수익률 기준 설명 텍스트 추가.

**변경 파일**:
- `frontend/src/pages/IndicatorSignalPage.tsx`

**상세**:
- "예측 기간: T+{N}일", "성공 기준: 매수→T+N일 상승, 매도→T+N일 하락"
- "수익률: 시그널 T+N일 수익률 평균"

---

### Step 7: MACD signal lookback 검증
DR.12 LOOKBACK_DAYS=150 확장 후 macd_signal 초기 날짜 존재 여부 검증.
- 해결 시: 추가 작업 불필요
- 미해결 시: start_date lookback 적용

## 5. 구현 순서

```
Step 2 (T+3 frequency) → Step 3 (RSI 해제) → Step 5 (기간 동기화) → Step 6 (성공률 검증)
→ Step 1 (지표 설명) → Step 4 (ATR 스케일) → Step 7 (MACD 검증)
```

## 6. 검증 방법

1. `python -m pytest` — 기존 681 tests 통과 + 새 테스트
2. `tsc --noEmit` + `vite build` — 프론트엔드 빌드
3. 브라우저 E2E: 시그널 T+3 필터, RSI 해제, ATR % 스케일, 성공률 기간 동기화
