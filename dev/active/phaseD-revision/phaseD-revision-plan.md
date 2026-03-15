# Phase D-rev: 지표 페이지 피드백 반영
> Last Updated: 2026-03-15
> Status: Planning
> Source: `docs/post-mvp-feedback.md` Phase D 섹션

## 1. Summary (개요)

**목적**: Phase D 프로덕션 리뷰 피드백 반영 — 전략(momentum/trend/mean_reversion) 기반 → **개별 지표(RSI/MACD/ATR+vol)** 기반 전환, 탭 통합, 레이아웃 개선, 정규화 버그 수정
**범위**: 지표별 시그널 생성 서비스(백엔드 신규), 성공률 재계산(백엔드 수정), API 수정, 프론트 탭/레이아웃 전면 개편
**원칙**: Phase E 진입 전 완료 — 기존 전략 코드는 삭제하지 않고 Phase E 전략 페이지에서 활용

## 2. Current State (현재 상태)

- **Phase D 12/12 완료** (`7dc230f` — 2026-03-15):
  - 3탭 구조: 지표 현황 / 시그널 타임라인 / 성공률
  - 시그널/성공률이 **전략(momentum/trend/mean_reversion)** 단위로 계산
  - `signal_daily` 테이블 기반 (strategy_id: momentum, trend, mean_reversion)
  - `indicator_analysis.py`에 RSI/MACD/ATR/vol_20 해석 규칙 이미 존재
  - `signal_accuracy_service.py`가 strategy_id 파라미터로 성공률 계산
- 테스트: 647 passed, 7 skipped, ruff clean
- Frontend: tsc --noEmit 0 errors, vite build 성공

## 3. Target State (목표 상태)

| 항목 | 현재 | 목표 |
|------|------|------|
| 탭 구조 | 3탭 (지표현황/시그널/성공률) | **2탭 (시그널/성공률)** |
| 시그널 단위 | 전략 (momentum/trend/mean_reversion) | **지표 (RSI/MACD/ATR+vol)** |
| 시그널 소스 | signal_daily 테이블 | **factor_daily → on-the-fly 시그널 생성** |
| 시그널 탭 레이아웃 | 전체 너비 차트 | **차트 3/4 + 설명 1/4, 시그널 수직 점선** |
| 성공률 탭 레이아웃 | 전략 카드 + 막대 차트 + 순위 테이블 | **차트 3/4 + 거래 성공/실패 테이블 1/4** |
| 정규화 | `?? 0`으로 빈 값 0 처리 (버그) | **null 필터링/보간** |
| ATR(+vol) | 일반 지표와 동일 처리 | **시그널탭=위험 구간 표시, 성공률탭=성공/실패만** |

## 4. Implementation Stages

### Stage A: Backend — 지표별 시그널 생성 (DR.1~DR.2)

**핵심 아키텍처 변경**: signal_daily 테이블 대신 factor_daily 데이터에서 on-the-fly로 지표 시그널 생성

1. **DR.1** 지표별 시그널 생성 서비스 `[L]`
   - `api/services/analysis/indicator_signal_service.py` 신규
   - `generate_indicator_signals(db, asset_id, indicator_id, start, end) → list[IndicatorSignal]`
   - factor_daily 데이터를 시계열로 스캔 → **전환점(transition)** 감지
   - **RSI**: 70 상향 돌파 → sell, 30 하향 돌파 → buy (이전값과 비교하여 교차 시점만)
   - **MACD**: histogram(macd - macd_signal) 부호 전환 → buy/sell (골든/데드크로스)
   - **ATR(+vol)**: 고변동성 구간 진입/이탈 감지 → warning (매매 시그널 아님)
   - 기존 `indicator_analysis.py` 규칙 재활용 (`_RSI_RULES`, `_ATR_PCT_RULES`)
   - DB 저장 없음 (on-the-fly 계산)
   - 테스트: `test_indicator_signal_service.py`

   **IndicatorSignal 구조**:
   ```python
   @dataclass
   class IndicatorSignal:
       date: datetime.date
       indicator_id: str       # "rsi_14", "macd", "atr_vol"
       signal: int             # 1 (buy), -1 (sell), 0 (warning)
       label: str              # "RSI 과매도 진입", "MACD 골든크로스"
       value: float            # 시그널 시점의 지표값
       entry_price: float      # 시그널 시점의 종가
   ```

2. **DR.2** 지표별 성공률 계산 서비스 수정 `[M]`
   - `signal_accuracy_service.py` 수정 — `indicator_id` 파라미터 지원
   - 새 함수: `compute_indicator_accuracy(db, asset_id, indicator_id, forward_days)`
   - DR.1의 시그널 목록 → forward return 계산 (기존 로직 재활용)
   - 기존 `compute_signal_accuracy()` (strategy_id 기반)는 Phase E 하위호환 유지
   - 테스트: `test_signal_accuracy.py` 확장

### Stage B: Backend — API + 비교 수정 (DR.3~DR.4)

3. **DR.3** 지표 비교 서비스 수정 `[M]`
   - `indicator_comparison.py` 수정
   - `DEFAULT_STRATEGY_IDS` → `DEFAULT_INDICATOR_IDS = ["rsi_14", "macd"]`
   - RSI vs MACD 성공률 비교 (ATR은 제외 — 성공률 산출 불가)
   - 기존 전략 비교 함수는 하위호환 유지
   - 테스트: `test_indicator_comparison.py` 수정

4. **DR.4** API 엔드포인트 수정 `[M]`
   - `routers/analysis.py` 수정
   - `GET /v1/analysis/indicator-signals` 신규 — 지표별 시그널 목록
   - `GET /v1/analysis/signal-accuracy` 수정 — `indicator_id` 파라미터 추가 (strategy_id와 택일)
   - `GET /v1/analysis/indicator-comparison` 수정 — 지표 비교로 전환
   - `schemas/analysis.py` 수정 — 새 요청/응답 스키마
   - 테스트: `test_analysis_router.py` 수정

### Stage C: Frontend — 탭 통합 + 레이아웃 (DR.5~DR.7)

5. **DR.5** 3탭 → 2탭 전환 + 전략 배제 `[L]`
   - `IndicatorSignalPage.tsx` 전면 수정
   - 탭: `시그널` (기존 지표현황+시그널타임라인 통합) / `성공률`
   - STRATEGIES 상수 제거, INDICATORS 상수 도입: `[{id: "rsi_14", label: "RSI"}, {id: "macd", label: "MACD"}, {id: "atr_vol", label: "ATR+변동성"}]`
   - API 호출: strategy_id → indicator_id 전환
   - `api/analysis.ts` 수정 — 새 API 함수 추가

6. **DR.6** 시그널 탭 레이아웃 `[M]`
   - 차트 영역 3/4 + 설명 패널 1/4 레이아웃
   - 가격 + 지표 오버레이 차트 (기존 IndicatorOverlayChart 수정)
   - **시그널 지점에 Y축 수직 점선** (Recharts `ReferenceLine` x={signalDate})
   - 설명 패널: 선택된 지표의 현재 해석 상태 + 시그널 이력 요약
   - ATR(+vol): 위험도 높은 구간을 `ReferenceArea`로 표시

7. **DR.7** 성공률 탭 레이아웃 `[M]`
   - 차트 영역 3/4 + 거래 테이블 1/4 레이아웃
   - 차트: 가격 + 시그널 포인트 (성공=녹색, 실패=적색 마커)
   - 우측 테이블: 각 거래별 날짜/방향/진입가/청산가/수익률/성공여부
   - AccuracyBarChart 수정 — 전략 → 지표별로 전환

### Stage D: Frontend — 버그 수정 + 특수 처리 (DR.8~DR.9)

8. **DR.8** 정규화 버그 수정 `[S]`
   - `IndicatorOverlayChart.tsx` — `applyTransform()` 수정
   - 현재: `(p.close as number) ?? 0`, `(p[f] as number) ?? 0` → 가격 없는 날짜에서 0으로 떨어짐
   - 수정: `undefined`/`null` 값은 변환에서 제외, `connectNulls` 활용
   - `mergeRawData()`에서 가격 없는 날짜의 `close`를 `undefined`로 유지

9. **DR.9** ATR(+vol) 특수 처리 `[S]`
   - 시그널 탭: 위험도 높은 구간을 ReferenceArea (반투명 빨간 배경)로 표시
   - 성공률 탭: ATR은 성공/실패 결과만 표시 (성공률 차트에서 제외)
   - 프론트에서 `indicator_id === "atr_vol"` 분기 처리

### Stage E: 통합 검증 (DR.10)

10. **DR.10** Phase D-rev 통합 검증 `[M]`
    - Backend: pytest 전체 통과 + ruff check clean
    - Frontend: tsc --noEmit + vite build 성공
    - 프로덕션 배포: git push → Railway/Vercel 자동 배포
    - 브라우저 E2E 체크리스트:
      1. 2탭 구조 (시그널/성공률) 확인
      2. RSI/MACD/ATR 지표 선택 → 시그널 표시
      3. 시그널 수직 점선 표시
      4. 3/4 + 1/4 레이아웃 (시그널 탭, 성공률 탭)
      5. 성공/실패 마커 + 거래 테이블
      6. 정규화 시 0으로 튀지 않음
      7. ATR 위험 구간 표시
      8. 챗봇 연동 동작

## 5. Task Breakdown

| # | Task | Size | 의존성 | Stage |
|---|------|------|--------|-------|
| DR.1 | 지표별 시그널 생성 서비스 | L | indicator_analysis.py 규칙 | A |
| DR.2 | 지표별 성공률 계산 수정 | M | DR.1 | A |
| DR.3 | 지표 비교 서비스 수정 | M | DR.2 | B |
| DR.4 | API 엔드포인트 수정 | M | DR.1, DR.2, DR.3 | B |
| DR.5 | 3탭→2탭 전환 + 전략 배제 | L | DR.4 | C |
| DR.6 | 시그널 탭 레이아웃 (3/4+1/4, 수직 점선) | M | DR.5 | C |
| DR.7 | 성공률 탭 레이아웃 (3/4+1/4, 거래 테이블) | M | DR.5 | C |
| DR.8 | 정규화 버그 수정 | S | - | D |
| DR.9 | ATR(+vol) 특수 처리 | S | DR.5, DR.6 | D |
| DR.10 | Phase D-rev 통합 검증 | M | DR.1~DR.9 전체 | E |

**Total**: 10 tasks (S:2, M:5, L:2)

## 6. Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| on-the-fly 시그널 생성 성능 | 응답 지연 | factor_daily는 7자산×500일 수준으로 소규모. 캐싱 불필요 |
| RSI/MACD 전환점 감지 로직 오류 | 시그널 누락/과다 | 이전일 대비 교차 여부로 명확하게 판단. 테스트 충분히 작성 |
| 기존 strategy 기반 API 하위호환 | Phase E 영향 | strategy_id 파라미터 유지, indicator_id와 택일 |
| 프론트 전면 개편 규모 | 작업량 과다 | 기존 컴포넌트 최대 재활용, 레이아웃만 변경 |

## 7. Dependencies

**내부**:
- `indicator_analysis.py` — RSI/MACD/ATR 해석 규칙 (재활용)
- `factor_repo.get_factors()` — 팩터 시계열 조회
- `price_repo.get_prices()` — 종가 조회 (성공률 계산)
- Phase C `chartActionStore` — 챗봇 연동

**외부 (신규 없음)**: 기존 패키지로 충분
