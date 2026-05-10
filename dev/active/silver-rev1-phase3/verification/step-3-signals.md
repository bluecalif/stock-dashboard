# Step 3 — SignalDetailPage 검증 Evidence

> Generated: 2026-05-10
> Verification: Puppeteer (`/tmp/pw_test/verify-p3-3.cjs`)

---

## G3.1 — SignalDetailPage 기본 렌더링

**명령**: 브라우저에서 `/silver/signals` 접속, QQQ 선택, RSI 탭

**Evidence**: `figures/step-3-signals-desktop.png`

**결과**:
- 자산 select: QQQ / SPY / KS200 / NVDA / GOOGL / TSLA / 005930 / 000660 (8종) ✓
- 지표 탭: [RSI] [MACD] [ATR] 3개 표시 ✓
- 차트: 가격(파랑) + RSI 오버레이(빨강), 시그널 마커 표시 ✓
- Silver 다크 톤 (--bg-app, --bg-card, CSS var) ✓

**통과 기준**: ✅ PASS

---

## G3.2 — 상태 라벨 표시

**명령**: RSI 탭에서 현재 RSI 값과 상태 라벨 확인

**Evidence**: `figures/step-3-signals-indicator-closeup.png`

**결과**:
```
현재 지표 — QQQ (나스닥 100)
RSI 14    83.26    [과매수]
```

- 상태 라벨: "과매수" (RSI > 70 조건 충족) ✓
- 구체적 수치: 83.26 병기 ✓
- MACD 탭 전환 시: "MACD 히스토그램 | 3.70 | [골든크로스]" ✓

**통과 기준**: ✅ PASS

---

## G3.3 — 성공률 탭 미노출

**명령**: SignalDetailPage 탭 목록 확인

**Evidence**: Puppeteer 로그 + `figures/step-3-signals-desktop.png` (탭 영역)

**결과**:
```
탭 목록: ['RSI', 'MACD', 'ATR']
성공률 탭: false
RSI: true, MACD: true, ATR: true
자산 옵션 수: 8
```

- "성공률" 탭 없음 ✓
- [RSI] [MACD] [ATR] 3개만 존재 ✓

**통과 기준**: ✅ PASS

---

## 추가 노트

- QQQ/SPY/NVDA/GOOGL/TSLA 팩터 데이터 부재 → `run_research.py --assets QQQ,SPY,NVDA,GOOGL,TSLA` 실행으로 해결
  - 실행 기간: 2024-05-10 ~ 2026-05-10 (2년)
  - 결과: 각 자산 factors + signals 성공적으로 생성
- `IndicatorCard` 재사용 (Silver CSS var 완전 호환)
- "매수/매도 추천" 표현 없음 (D-21 준수) ✓
- 성공률 관련 함수 임포트 없음 (`fetchIndicatorAccuracy`, `fetchIndicatorComparisonV2` 미사용) ✓
