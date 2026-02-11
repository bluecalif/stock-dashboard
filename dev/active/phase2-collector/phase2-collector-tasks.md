# Phase 2 Tasks
> Last Updated: 2026-02-11
> Status: Complete

## Overview
- **Total Tasks**: 7
- **Size Distribution**: S: 2, M: 3, L: 1, XL: 0 (+ 통합 테스트 M: 1)
- **DB 필수**: 2.2, 2.3, 2.5, 2.6, 2.7

---

## Task 2.1: 재시도 강화 + 로깅 설정 `[S]`
- **Dependencies**: 없음
- **Commit**: `[phase2-collector] Step 2.1: 재시도 강화 + 로깅 설정`

### Checklist
- [ ] `config/settings.py` 수정
  - [ ] `fdr_max_retries: int = 3` 필드 추가
  - [ ] `fdr_base_delay: float = 1.0` 필드 추가
- [ ] `config/logging.py` 생성
  - [ ] `setup_logging(level)` 함수
  - [ ] 포맷: `%(asctime)s %(name)s %(levelname)s %(message)s`
  - [ ] stdout 핸들러
- [ ] `collector/fdr_client.py` 수정
  - [ ] `MAX_RETRIES`, `BASE_DELAY` 상수 → `settings.fdr_max_retries`, `settings.fdr_base_delay`
  - [ ] jitter 추가: `delay * (1 + random() * 0.3)`
- [ ] 기존 테스트 통과 확인
- [ ] `ruff check .` 통과

---

## Task 2.2: idempotent UPSERT `[M]` ★최우선
- **Dependencies**: 2.1
- **Commit**: `[phase2-collector] Step 2.2: idempotent UPSERT`

### Checklist
- [ ] `collector/ingest.py` 수정
  - [ ] `_bulk_insert()` → `_upsert()` 변경
  - [ ] `from sqlalchemy.dialects.postgresql import insert` 사용
  - [ ] `insert().on_conflict_do_update()` 구현
    - [ ] conflict 키: `(asset_id, date, source)`
    - [ ] update 컬럼: `open, high, low, close, volume, ingested_at`
  - [ ] chunk 처리 (1000행 단위)
  - [ ] `ingest_asset()` 내 `_bulk_insert` → `_upsert` 호출 변경
- [ ] `tests/unit/test_ingest.py` 수정
  - [ ] 기존 테스트: `_bulk_insert` → `_upsert` 참조 업데이트
  - [ ] 신규 테스트: `test_upsert_uses_on_conflict` (mock으로 SQL 구조 검증)
- [ ] `ruff check .` + `pytest` 통과

---

## Task 2.3: job_run 기록 + 부분 실패 허용 `[M]`
- **Dependencies**: 2.2
- **Commit**: `[phase2-collector] Step 2.3: job_run 기록 + 부분 실패`

### Checklist
- [ ] `collector/ingest.py` 수정
  - [ ] `_create_job_run(session, job_name)` 헬퍼 추가
    - [ ] `JobRun` 생성: `status="running"`, `started_at=now()`
    - [ ] `session.flush()` → `job_id` 반환
  - [ ] `_finish_job_run(session, job_id, results)` 헬퍼 추가
    - [ ] 전체 성공 → `status="success"`
    - [ ] 일부 실패 → `status="partial_failure"`
    - [ ] 전체 실패 → `status="failure"`
    - [ ] `ended_at=now()`
    - [ ] `error_message` = 실패 자산 요약 JSON
  - [ ] `ingest_all()` 수정
    - [ ] 시작 시 `_create_job_run()` 호출
    - [ ] 완료 시 `_finish_job_run()` 호출
  - [ ] `IngestResult`에 `warnings: list[str]` 필드 추가
- [ ] `tests/unit/test_ingest.py` 추가
  - [ ] `test_job_run_created_on_ingest_all`
  - [ ] `test_job_run_partial_failure_status`
- [ ] `ruff check .` + `pytest` 통과

---

## Task 2.4: 정합성 검증 강화 `[M]`
- **Dependencies**: 없음 (2.1과 병렬 가능)
- **Commit**: `[phase2-collector] Step 2.4: 정합성 검증 강화`

### Checklist
- [ ] `collector/validators.py` 수정
  - [ ] `ValidationResult`에 `flagged_dates: list[str]` 필드 추가 (default=[])
  - [ ] 날짜 갭 검출 추가
    - [ ] `_check_date_gaps(df)` 함수
    - [ ] 자산 category 파라미터 (crypto=date_range, 기타=bdate_range)
    - [ ] 누락 영업일 목록을 warnings에 추가
    - [ ] 결과: 저장 허용 (경고만)
  - [ ] 급등락 플래그 추가
    - [ ] `_check_price_spike(df, threshold=0.3)` 함수
    - [ ] `close.pct_change().abs() > threshold` 검출
    - [ ] 해당 날짜를 `flagged_dates`에 추가
    - [ ] 결과: 저장 허용 (경고만)
  - [ ] `validate_ohlcv()` 시그니처에 `category: str = "stock"` 파라미터 추가
- [ ] `tests/unit/test_validators.py` 추가
  - [ ] `test_date_gap_detection` — 영업일 갭 경고
  - [ ] `test_no_gap_for_crypto` — BTC 매일 거래 기준 갭 검사
  - [ ] `test_price_spike_warning` — 30% 이상 변동 경고
  - [ ] `test_flagged_dates_populated` — flagged_dates에 날짜 기록
- [ ] 기존 테스트 깨지지 않음 확인
- [ ] `ruff check .` + `pytest` 통과

---

## Task 2.5: 수집 실행 스크립트 + 스모크 테스트 `[S]`
- **Dependencies**: 2.2, 2.3
- **Commit**: `[phase2-collector] Step 2.5: CLI 수집 스크립트`

### Checklist
- [ ] `scripts/collect.py` 생성
  - [ ] `argparse` 인자 처리
    - [ ] `--start` (필수): 시작 날짜
    - [ ] `--end` (필수): 종료 날짜
    - [ ] `--assets` (선택): 콤마 구분 자산 ID 목록
  - [ ] 로깅 초기화 (`config.logging.setup_logging`)
  - [ ] DB 세션 생성 (`db.session.SessionLocal`)
  - [ ] `ingest_all()` 또는 개별 `ingest_asset()` 호출
  - [ ] 결과 요약 출력 (성공/실패 수, 총 행 수, 소요 시간)
- [ ] 스모크 테스트 실행
  - [ ] `python scripts/collect.py --start 2026-02-01 --end 2026-02-11`
  - [ ] 7개 자산 수집 성공 확인
  - [ ] 같은 명령 재실행 → UPSERT로 에러 없음 확인
  - [ ] DB row count 확인
- [ ] `ruff check .` 통과

---

## Task 2.6: 3년 백필 + 검증 `[L]`
- **Dependencies**: 2.5
- **Commit**: `[phase2-collector] Step 2.6: 3년 백필 완료`

### Checklist
- [ ] 백필 실행
  - [ ] `python scripts/collect.py --start 2023-02-11 --end 2026-02-11`
  - [ ] FDR 타임아웃 대비: 자산별 개별 실행 또는 연도별 분할 고려
- [ ] 데이터 검증 쿼리
  - [ ] `SELECT asset_id, count(*), min(date), max(date) FROM price_daily GROUP BY asset_id`
  - [ ] 자산별 예상 행 수 vs 실제 행 수 비교
  - [ ] 주요 결측 구간 확인
- [ ] `job_run` 테이블에 백필 작업 기록 확인
- [ ] 검증 결과 기록 (커밋 메시지 또는 docs/backfill-report.md)

---

## Task 2.7: 통합 테스트 `[M]`
- **Dependencies**: 2.3 (job_run), 2.5 이후 권장
- **Commit**: `[phase2-collector] Step 2.7: DB 통합 테스트`

### Checklist
- [ ] `tests/integration/__init__.py` 생성
- [ ] `tests/integration/conftest.py` 생성
  - [ ] `@pytest.fixture` DB 세션 (실제 Railway PostgreSQL)
  - [ ] `INTEGRATION_TEST=1` 환경변수 게이트
  - [ ] `pytest.mark.skipif(not os.environ.get("INTEGRATION_TEST"))` 데코레이터
- [ ] `tests/integration/test_ingest_db.py` 생성
  - [ ] `test_upsert_idempotent` — 같은 데이터 2회 upsert → 1행만 존재
  - [ ] `test_upsert_updates_ingested_at` — 재수집 시 ingested_at 갱신
  - [ ] `test_job_run_recorded` — ingest_all 후 job_run 레코드 존재
  - [ ] `test_partial_failure_recorded` — 일부 실패 시 partial_failure 상태
- [ ] `INTEGRATION_TEST=1 python -m pytest tests/integration/ -v` 통과
- [ ] 일반 `pytest` 실행 시 통합 테스트 스킵 확인

---

## 실행 순서

```
[Stage A — 병렬]
2.1 (재시도+로깅) ──┐
2.4 (검증 강화) ────┤
                    ↓
[Stage B — 순차]
2.2 (UPSERT) ★ ────→ 2.3 (job_run)
                          ↓
[Stage C — 순차]
2.5 (스크립트+스모크) ──→ 2.6 (3년 백필)
                          ↓
2.7 (통합 테스트)
```

## Progress Tracker

| Task | Size | Status | Commit |
|------|------|--------|--------|
| 2.1 재시도+로깅 | S | [x] Done | `21eb554` |
| 2.2 UPSERT | M | [x] Done | `9bb7765` |
| 2.3 job_run | M | [x] Done | `90c5a67` |
| 2.4 검증 강화 | M | [x] Done | `21eb554` |
| 2.5 스크립트 | S | [x] Done | `2bc5889` |
| 2.6 3년 백필 | L | [x] Done | `6bcad30` |
| 2.7 통합 테스트 | M | [x] Done | `6bcad30` |
