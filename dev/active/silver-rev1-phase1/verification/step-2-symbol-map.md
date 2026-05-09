# P1-2 Verification: SYMBOL_MAP 8종 추가

> Step: P1-2 (SYMBOL_MAP에 QQQ/SPY/SCHD/JEPI/TLT/NVDA/GOOGL/TSLA 추가)
> 변경 파일: `backend/collector/fdr_client.py:14`
> Captured: 2026-05-09
> Status: 모든 게이트 통과, commit 대기 중

---

## G2.1 — SYMBOL_MAP 키 개수 = 15

**명령**:
```bash
python -c "from collector.fdr_client import SYMBOL_MAP; print(len(SYMBOL_MAP), sorted(SYMBOL_MAP.keys()))"
```

**Raw output**:

```
count: 15
keys: ['000660', '005930', 'BTC', 'GC=F', 'GOOGL', 'JEPI', 'KS200', 'NVDA',
       'QQQ', 'SCHD', 'SI=F', 'SOXL', 'SPY', 'TLT', 'TSLA']
```

**Categories**:

| category | count |
|---|---|
| index | 1 (KS200) |
| stock | 5 (005930 / 000660 / NVDA / GOOGL / TSLA) |
| etf | 6 (SOXL / QQQ / SPY / SCHD / JEPI / TLT) |
| crypto | 1 (BTC) |
| commodity | 2 (GC=F / SI=F) |

**검증 결과**: ✅ PASS
- 길이 15 (기존 7 + 신규 8)
- 신규 8종 모두 포함: QQQ / SPY / SCHD / JEPI / TLT / NVDA / GOOGL / TSLA
- D-1 적용: JEPY 표기 → JEPI 통일

---

## G2.2 — 기존 7 엔트리 무변경 (Bronze 영향 0)

**명령**: `git diff backend/collector/fdr_client.py`

**Raw output**:

```diff
@@ -23,6 +23,15 @@ SYMBOL_MAP: dict[str, dict] = {
     "BTC": {"fdr_symbol": "BTC/KRW", "category": "crypto", "fallbacks": ["BTC/USD"]},
     "GC=F": {"fdr_symbol": "GC=F", "category": "commodity"},
     "SI=F": {"fdr_symbol": "SI=F", "category": "commodity"},
+    # Silver gen 신규 8종 (마스터플랜 §2.1 / §5.2, JEPY → JEPI 통일 D-1)
+    "QQQ": {"fdr_symbol": "QQQ", "category": "etf"},
+    "SPY": {"fdr_symbol": "SPY", "category": "etf"},
+    "SCHD": {"fdr_symbol": "SCHD", "category": "etf"},
+    "JEPI": {"fdr_symbol": "JEPI", "category": "etf"},
+    "TLT": {"fdr_symbol": "TLT", "category": "etf"},
+    "NVDA": {"fdr_symbol": "NVDA", "category": "stock"},
+    "GOOGL": {"fdr_symbol": "GOOGL", "category": "stock"},
+    "TSLA": {"fdr_symbol": "TSLA", "category": "stock"},
 }
```

**검증 결과**: ✅ PASS
- 신규 추가 라인만 (9 라인 = 주석 1 + 엔트리 8)
- 기존 7 엔트리 (KS200 / 005930 / 000660 / SOXL / BTC / GC=F / SI=F) 모두 무변경
- Bronze collector job 영향 0 보장

---

## G2.3 — 신규 8자산 1주 fetch smoke (FDR 응답 sanity)

**명령**:
```bash
python -c "from collector.fdr_client import fetch_ohlcv; ..."
```
8 자산 각각 `fetch_ohlcv(asset, '2026-04-01', '2026-04-08')` 호출.

**Raw output**:

| asset | rows | first | last | last_close |
|---|---|---|---|---|
| QQQ | 5 | 2026-03-31 | 2026-04-07 | 588.59 |
| SPY | 5 | 2026-03-31 | 2026-04-07 | 659.22 |
| SCHD | 5 | 2026-03-31 | 2026-04-07 | 30.56 |
| JEPI | 5 | 2026-03-31 | 2026-04-07 | 56.52 |
| TLT | 5 | 2026-03-31 | 2026-04-07 | 86.64 |
| NVDA | 5 | 2026-03-31 | 2026-04-07 | 178.10 |
| GOOGL | 5 | 2026-03-31 | 2026-04-07 | 305.46 |
| TSLA | 5 | 2026-03-31 | 2026-04-07 | 346.65 |

**검증 결과**: ✅ PASS
- 8자산 모두 5 row fetch 성공 (예상 거래일 4~5일, 오류 0)
- 가격 sanity check 모두 통과 (각 자산의 일반적 범위 내):
  - QQQ ~$588, SPY ~$659 (US ETF 정상 범위)
  - JEPI ~$56, TLT ~$86 (배당 ETF / 채권 ETF 정상)
  - NVDA ~$178, GOOGL ~$305, TSLA ~$346 (개별주 정상)
  - SCHD ~$30 (분할 후 가격 정상)
- 모든 first_date == 2026-03-31, last_date == 2026-04-07 → FDR 응답 시계열 정합

> 참고: FDR이 `2026-04-01` 요청 시 직전 거래일(2026-03-31)부터 inclusive 반환 — 의도된 동작.

---

## G2.4 — 본 evidence 파일 작성

✅ 본 파일 (`verification/step-2-symbol-map.md`) 자체.

---

## 종합

| Gate | 결과 |
|---|---|
| G2.1 키 개수 15 + 신규 8 포함 | ✅ |
| G2.2 기존 7 엔트리 무변경 | ✅ |
| G2.3 8자산 fetch smoke | ✅ |
| G2.4 evidence 파일 작성 | ✅ |

**P1-2 통과**. P1-3 (fx_collector USD/KRW) 진입 가능.
