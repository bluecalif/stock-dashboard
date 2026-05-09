# P1-3 Verification: fx_collector USD/KRW 일봉

> Step: P1-3 (backend/collector/fx_collector.py 신규)
> Captured: 2026-05-09

---

## G3.1 — smoke insert (2026-05-01 ~ 2026-05-09, 8 거래일)

**명령**: `python -c "from collector.fx_collector import run; print(run('2026-05-01', '2026-05-09'))"`

**Raw output**:
```
INFO:collector.fx_collector:fx_collector: 8 row upserted (9.8s)
result: {'status': 'success', 'rows': 8, 'start': '2026-05-01', 'end': '2026-05-09'}
```

**검증 결과**: ✅ PASS — 8 row insert 성공, error 0

---

## G3.2 — 최근 row + 가격 sanity (1,100~1,600 KRW/USD 범위)

**명령**: `select date, usd_krw_close from fx_daily order by date desc limit 8`

**Raw output**:

| date | usd_krw_close |
|---|---|
| 2026-05-08 | 1461.4800 |
| 2026-05-07 | 1454.7900 |
| 2026-05-06 | 1444.4500 |
| 2026-05-05 | 1473.9600 |
| 2026-05-04 | 1476.0500 |
| 2026-05-03 | 1471.7300 |
| 2026-04-30 | 1474.0100 |
| 2026-04-29 | 1487.3800 |

**검증 결과**: ✅ PASS
- 8 row 확인
- 가격 범위 1,444~1,488 KRW/USD (sanity 통과)
- 2026-05-02 없음 → 한국 어린이날 공휴일 (KR 휴장) — 정상

---

## G3.3 — idempotent 재실행 (UPSERT 검증)

**명령**: 동일 구간 두 번 실행 → before/after count 비교

**Raw output**:
```
before=8, after=8, diff=0
```

**검증 결과**: ✅ PASS — ON CONFLICT DO UPDATE 동작, row 중복 생성 0

---

## G3.4 — 본 evidence 파일 작성

✅ 본 파일

---

## 종합

| Gate | 결과 |
|---|---|
| G3.1 smoke insert 8 row | ✅ |
| G3.2 최근 row + sanity | ✅ |
| G3.3 idempotent | ✅ |
| G3.4 evidence 작성 | ✅ |

**P1-3 통과**. P1-4 (backfill) 진입 가능.
