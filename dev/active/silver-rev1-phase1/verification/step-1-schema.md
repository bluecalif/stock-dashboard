# P1-1 Verification: Schema Migration

> Step: P1-1 (Alembic migration: asset_master 5컬럼 + fx_daily)
> Commit: `7d457a2` ([silver-rev1-phase1] Step 1: AssetMaster 5컬럼 + FxDaily + migration)
> Migration: `d8334483342c_silver_rev1_schema_changes.py`
> Captured: 2026-05-09
> DB: Railway prod (mainline.proxy.rlwy.net:34025/railway)

---

## G1.1 — asset_master 10컬럼 등록

**명령**:
```bash
python -c "from sqlalchemy import inspect; from db.session import engine; ..."
```

**Raw output**:

| name | type | nullable | default |
|---|---|---|---|
| asset_id | VARCHAR(20) | False |  |
| name | VARCHAR(100) | False |  |
| category | VARCHAR(20) | False |  |
| source_priority | JSON | False |  |
| is_active | BOOLEAN | False |  |
| currency | VARCHAR(8) | False | `'KRW'::character varying` |
| annual_yield | NUMERIC(6, 4) | False | `'0'::numeric` |
| history_start_date | DATE | True |  |
| allow_padding | BOOLEAN | False | `false` |
| display_name | VARCHAR(64) | True |  |

**검증 결과**: ✅ PASS
- 컬럼 10개 (기존 5 + 신규 5)
- 신규 5컬럼 모두 nullable=True 또는 server_default 명시 (Bronze 영향 0 보장)
  - currency / annual_yield / allow_padding: server_default
  - history_start_date / display_name: nullable=True

---

## G1.2 — fx_daily 신규 + PK=date

**Raw output**:

```
fx_daily exists: True
```

| name | type | nullable | default |
|---|---|---|---|
| date | DATE | False |  |
| usd_krw_close | NUMERIC(10, 4) | False |  |
| created_at | TIMESTAMP | False | `now()` |

PK constraint: `{'constrained_columns': ['date'], 'name': 'fx_daily_pkey'}`

**검증 결과**: ✅ PASS
- 테이블 존재
- PK = `date` (단일 컬럼)
- created_at 서버 default `now()` 적용

---

## G1.3 — 기존 row DEFAULT 자동 적용 (Bronze 영향 0)

**명령**:
```sql
select asset_id, currency, annual_yield, allow_padding, display_name, history_start_date
from asset_master where asset_id='KS200'
```

**Raw output**:

| asset_id | currency | annual_yield | allow_padding | display_name | history_start_date |
|---|---|---|---|---|---|
| KS200 | KRW | 0.0000 | False | NULL | NULL |

**검증 결과**: ✅ PASS
- `currency='KRW'` (server_default 적용)
- `annual_yield=0.0000` (server_default 적용)
- `allow_padding=False` (server_default 적용)
- `display_name`, `history_start_date`는 nullable → NULL (P1-4 seed 스크립트에서 채울 예정)

---

## G1.4 — Downgrade reversibility (offline SQL)

**명령**:
```bash
alembic downgrade d8334483342c:c4d2e5f6a789 --sql
```

**Raw output**:

```sql
INFO  Running downgrade d8334483342c -> c4d2e5f6a789, silver_rev1_schema_changes
-- Running downgrade d8334483342c -> c4d2e5f6a789

ALTER TABLE asset_master DROP COLUMN display_name;
ALTER TABLE asset_master DROP COLUMN allow_padding;
ALTER TABLE asset_master DROP COLUMN history_start_date;
ALTER TABLE asset_master DROP COLUMN annual_yield;
ALTER TABLE asset_master DROP COLUMN currency;
DROP TABLE fx_daily;

UPDATE alembic_version SET version_num='c4d2e5f6a789'
  WHERE alembic_version.version_num = 'd8334483342c';
COMMIT;
```

**검증 결과**: ✅ PASS
- 5건 `DROP COLUMN` (역순 — display_name → currency)
- `DROP TABLE fx_daily`
- `UPDATE alembic_version` (head 복귀)
- 정확한 reverse, 데이터 손실 외 reversible

---

## G1.5 — Upgrade SQL (참고)

**명령**: `alembic upgrade c4d2e5f6a789:d8334483342c --sql`

**Raw output**:

```sql
CREATE TABLE fx_daily (
    date DATE NOT NULL,
    usd_krw_close NUMERIC(10, 4) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (date)
);

ALTER TABLE asset_master ADD COLUMN currency VARCHAR(8) DEFAULT 'KRW' NOT NULL;
ALTER TABLE asset_master ADD COLUMN annual_yield NUMERIC(6, 4) DEFAULT '0' NOT NULL;
ALTER TABLE asset_master ADD COLUMN history_start_date DATE;
ALTER TABLE asset_master ADD COLUMN allow_padding BOOLEAN DEFAULT false NOT NULL;
ALTER TABLE asset_master ADD COLUMN display_name VARCHAR(64);

UPDATE alembic_version SET version_num='d8334483342c' WHERE alembic_version.version_num = 'c4d2e5f6a789';
```

마스터플랜 §5.1과 정확히 일치. ✅

---

## Alembic head 확인

```
alembic_version: d8334483342c (head)
```

✅ Migration 적용 완료, prod 라이브 상태.

---

## 종합

| Gate | 결과 |
|---|---|
| G1.1 asset_master 10컬럼 | ✅ |
| G1.2 fx_daily + PK=date | ✅ |
| G1.3 기존 row DEFAULT 적용 | ✅ |
| G1.4 downgrade reversibility | ✅ |
| G1.5 verification 작성 | ✅ (본 파일) |

**P1-1 통과**. P1-2 (SYMBOL_MAP) 진입 가능.
