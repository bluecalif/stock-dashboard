# Phase 2 Context
> Last Updated: 2026-02-11
> Status: In Progress (Stage D)

## 핵심 파일

### 수정 대상
| 파일 | 변경 내용 |
|------|-----------|
| `backend/config/settings.py` | retry 설정 필드 추가 (`fdr_max_retries`, `fdr_base_delay`) |
| `backend/collector/fdr_client.py` | settings 연동 + jitter 추가 |
| `backend/collector/ingest.py` | `_bulk_insert()` → `_upsert()`, job_run 기록, chunk 처리 |
| `backend/collector/validators.py` | 날짜 갭 검출 + 급등락 플래그 추가 |
| `backend/tests/unit/test_ingest.py` | UPSERT mock 테스트 |
| `backend/tests/unit/test_validators.py` | 새 검증 규칙 테스트 |

### 신규 생성
| 파일 | 용도 |
|------|------|
| `backend/config/logging.py` | 로깅 초기화 유틸 |
| `backend/scripts/collect.py` | CLI 수집 진입점 |
| `backend/tests/integration/__init__.py` | 통합 테스트 패키지 |
| `backend/tests/integration/conftest.py` | 통합 테스트 fixtures (INTEGRATION_TEST 게이트, SAVEPOINT 롤백) |
| `backend/tests/integration/test_ingest_db.py` | DB 통합 테스트 (4개) |

### 신규 생성 (Stage D: 2.8~2.10)
| 파일 | 용도 |
|------|------|
| `backend/collector/alerting.py` | Discord webhook 알림 전송 |
| `backend/scripts/healthcheck.py` | 자산별 데이터 신선도 검증 |
| `backend/scripts/daily_collect.bat` | Windows 일일 수집 배치 래퍼 |
| `backend/scripts/register_scheduler.bat` | schtasks 등록 스크립트 |
| `.env.example` | 환경변수 템플릿 |

### 수정 대상 (Stage D)
| 파일 | 변경 내용 |
|------|-----------|
| `backend/config/settings.py` | `alert_webhook_url` 필드 추가 |
| `backend/config/logging.py` | JSON 포맷터 추가 |
| `backend/collector/ingest.py` | 실패 시 알림 호출 |
| `.gitignore` | `logs/` 추가 |

### 참조 (읽기 전용)
| 파일 | 참조 내용 |
|------|-----------|
| `backend/db/models.py` | `PriceDaily` PK 구조, `JobRun` 필드 |
| `backend/db/session.py` | `SessionLocal`, `engine` |
| `backend/scripts/seed_assets.py` | UPSERT 패턴 참조 (session.get + 조건부 add) |
| `docs/masterplan-v0.md` §5.2 | "동일 키 중복 시 최신 ingest 우선" |
| `docs/masterplan-v0.md` §9 | 실패 복구: 지수 백오프, idempotent UPSERT, 부분 성공 |

## 핵심 결정사항

### UPSERT 방식
- **선택**: PostgreSQL `INSERT ... ON CONFLICT DO UPDATE` (SQLAlchemy `postgresql.insert`)
- **이유**: seed_assets.py의 `session.get()` 방식은 row-by-row라 3년 백필에 비효율. bulk UPSERT가 성능상 유리.
- **충돌 키**: `(asset_id, date, source)` — PriceDaily의 composite PK

### 갱신 대상 컬럼
- `open, high, low, close, volume, ingested_at` — 가격 데이터 전체 + 수집 시각
- `ingested_at`은 항상 현재 시각으로 갱신 (최신 수집 시점 추적)

### 배치 크기
- 1000행/chunk — 3년 데이터 (~750행/자산)이면 1 chunk로 처리 가능하지만 안전 마진

### job_run 상태값
- `running` → `success` | `partial_failure` | `failure`
- `partial_failure`: 1개 이상 자산 실패 + 1개 이상 성공

### 검증 신규 규칙
- 날짜 갭: `pandas.bdate_range` 대비 누락 영업일 검출 (경고 — 저장 허용)
  - crypto(`BTC`)는 매일 거래이므로 bdate_range 대신 date_range 사용
- 급등락: `pct_change().abs() > 0.3` (30% 이상 변동 — 경고)

### 통합 테스트 게이트
- `INTEGRATION_TEST=1` 환경변수가 설정된 경우에만 실행
- `pytest.mark.skipif`로 게이트 처리

### Step 2.9 구현 내역
- `backend/scripts/daily_collect.bat` — 신규: venv 활성화 + collect.py T-7~T + 로그 파일 출력
- `backend/scripts/register_scheduler.bat` — 신규: schtasks 등록 (매일 18:00, 관리자 권한)
- `logs/.gitkeep` — 신규: 로그 디렉토리 유지

### Step 2.8 구현 내역
- `backend/collector/alerting.py` — 신규: Discord webhook 전송 + 메시지 포맷팅
- `backend/config/logging.py` — 수정: `JsonFormatter` 클래스, `fmt` 파라미터 추가
- `backend/collector/ingest.py` — 수정: `_finish_job_run()`에서 failure 시 Discord 알림 호출
- `.env.example` (루트) — 신규: 환경변수 템플릿
- `.gitignore` — 수정: `logs/` 추가
- `backend/tests/unit/test_alerting.py` — 신규: alerting 테스트 5개
- `backend/tests/unit/test_logging.py` — 신규: JsonFormatter 테스트 2개
- 알림 라이브러리: `urllib.request` (stdlib) 사용 — 추가 의존성 없음

### Stage D 결정사항

#### 알림 정책
- Discord Webhook 사용 (마스터플랜 §9, §17)
- 알림 실패가 수집 프로세스를 중단하면 안 됨 (try/except로 격리)
- `ALERT_WEBHOOK_URL`이 비어있으면 알림 스킵
- **[배포 체크리스트]** 운영 환경에서 반드시 실제 Discord webhook URL 설정 필요

#### 스케줄러 정책
- Windows Task Scheduler 사용 (마스터플랜 §4)
- 매일 18:00 KST (장 마감 15:30 + 2.5시간 여유)
- 최근 7일 수집 (갭 방지용 overlap — UPSERT이므로 안전)
- 로그 파일: `logs/collect_YYYYMMDD.log`

#### 신선도 기준
- 주식/인덱스/ETF/커모디티: 전 영업일 기준
- 크립토(BTC): 전일 기준 (매일 거래)
- T-1 기준으로 1일 이상 누락 시 STALE 판정

## 마스터플랜 매핑

| 마스터플랜 절 | Phase 2 태스크 |
|---------------|----------------|
| §5.2 동일 키 중복 시 최신 우선 | 2.2 UPSERT |
| §7.1 전처리: 캘린더 정렬, 결측 처리 | 2.4 검증 강화 |
| §7.1 이상치 플래그 | 2.4 급등락 검출 |
| §9 지수 백오프 재시도 | 2.1 재시도 강화 |
| §9 idempotent UPSERT | 2.2 UPSERT |
| §9 부분 성공 허용 | 2.3 job_run |
| §9 JSON 로그 | 2.8 JSON 로깅 전환 |
| §9 실패 알림(Discord Webhook) | 2.8 알림 |
| §4 Windows Task Scheduler | 2.9 스케줄러 |
| §9 작업별 성공/실패율 | 2.10 신선도 체크 |
| §12 2주차: 수집기 안정화, 정합성/복구 | Phase 2 전체 |
