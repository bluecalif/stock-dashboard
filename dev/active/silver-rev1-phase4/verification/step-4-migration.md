# P4-4 backtests.py 제거 + DROP migration Verification

> Date: 2026-05-10

---

## G4.1 — Migration SQL 검증

**명령**: `cat backend/db/alembic/versions/c9b884d01cb4_drop_backtest_tables.py`

**Raw output**:
```python
"""drop_backtest_tables

Revision ID: c9b884d01cb4
Revises: d8334483342c
"""

def upgrade() -> None:
    # FK 의존성 순서: trade_log → equity_curve → run
    op.drop_table("backtest_trade_log")
    op.drop_table("backtest_equity_curve")
    op.drop_table("backtest_run")

def downgrade() -> None:
    # rollback: backtest_run → equity_curve → trade_log 재생성
    op.create_table("backtest_run", ...)
    op.create_table("backtest_equity_curve", ...)
    op.create_table("backtest_trade_log", ...)
```

**검증 결과**: ✅ PASS — DROP TABLE 3개 포함, FK 의존성 순서 준수

---

## G4.2 — Migration 적용 후 테이블 없음 확인

**명령**:
```python
from db.session import SessionLocal
db = SessionLocal()
result = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'backtest_%'"))
rows = result.fetchall()
print('backtest tables:', rows)
```

**Raw output**:
```
backtest tables: []
```

**검증 결과**: ✅ PASS — 결과 0행. backtest_* 테이블 전부 DROP됨 (Railway prod DB)

> **참고**: 이 프로젝트는 단일 Railway DB를 사용하므로 `alembic upgrade head`가 prod에 직접 적용됨.

---

## G4.3 — backtests 라우터 제거 후 서버 기동

**명령**: `curl -s http://localhost:8000/v1/health`

**Raw output**:
```json
{"status":"ok","db":"connected"}
```

**검증 결과**: ✅ PASS — backtests.py 삭제 + main.py import 제거 후 서버 정상 기동

---

## 변경 내용

| 파일 | 변경 |
|------|------|
| `backend/api/routers/backtests.py` | 삭제 |
| `backend/api/main.py` | `backtests` import/include 제거 |
| `backend/db/alembic/versions/c9b884d01cb4_drop_backtest_tables.py` | 신규 — DROP migration |

**Alembic chain**: `d8334483342c` → `c9b884d01cb4` (head)
