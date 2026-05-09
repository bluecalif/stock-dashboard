# Phase 2: 수집 파이프라인 완성
> Last Updated: 2026-02-11
> Status: In Progress
> Current Step: 2.9 (Stage D)

## 1. Summary (개요)

### 목적
Phase 1에서 구축한 수집 파이프라인 골격(fetch → validate → store)을 프로덕션 수준으로 완성한다.

### 범위
- collector 모듈 고도화 (UPSERT, 재시도 강화, 검증 강화)
- job_run 이력 추적
- 3년 히스토리컬 데이터 백필
- 통합 테스트
- **운영화**: 실패 알림, 일일 스케줄러, 데이터 신선도 감시 (Stage D — 2.8~2.10)

### 예상 결과물
- 7개 자산 × 3년 일봉 데이터가 Railway PostgreSQL에 적재
- 재실행 안전한 idempotent 파이프라인
- 수집 이력이 job_run 테이블에 기록
- CLI 수집 스크립트 (`scripts/collect.py`)
- Discord 실패 알림 + JSON 구조화 로깅
- Windows Task Scheduler 일일 자동 수집
- 데이터 신선도 자동 체크

## 2. Current State (현재 상태)

### 구현 완료 (Phase 1)
- `collector/fdr_client.py`: FDR 래퍼, 7개 자산, BTC fallback, 기본 재시도 (3회)
- `collector/validators.py`: 8가지 OHLCV 검증 규칙
- `collector/ingest.py`: fetch → validate → INSERT 파이프라인
- `db/models.py`: 8개 테이블 ORM (JobRun 포함)
- `config/settings.py`: Pydantic Settings (DATABASE_URL, FDR_TIMEOUT 등)
- 단위 테스트 25개 통과

### 핵심 문제점
1. **INSERT only** — 재실행 시 PK 충돌 에러
2. **job_run 미사용** — 테이블만 존재, 기록 로직 없음
3. **로깅 미설정** — `logging.getLogger()` 호출만 있고 포맷터/핸들러 미구성
4. **검증 미흡** — 날짜 갭, 급등락 미검출
5. **실데이터 미검증** — 모든 테스트가 mock 기반

## 3. Target State (목표 상태)

- `ingest.py`가 UPSERT 수행 → 같은 기간 재실행 시 에러 없이 최신 데이터 반영
- 모든 수집 작업이 `job_run` 테이블에 시작/종료/상태 기록
- 검증기가 날짜 갭과 급등락을 경고로 플래그
- 3년 백필 완료 (7 자산 × ~750 거래일)
- CLI 스크립트로 수동/자동 수집 실행 가능

## 4. Implementation Phases (구현 단계)

### Stage A: 인프라 보강 (2.1, 2.4 — 병렬)
- 재시도 설정 외부화 + jitter + 로깅 셋업
- 검증 규칙 추가 (갭, 급등락)

### Stage B: 핵심 로직 (2.2, 2.3 — 순차)
- UPSERT 구현 (최우선)
- job_run 기록 통합

### Stage C: 검증 + 실행 (2.5, 2.6, 2.7)
- CLI 스크립트 + 스모크 테스트
- 3년 백필 실행
- DB 통합 테스트

### Stage D: 운영화 (2.8, 2.9, 2.10)
- Discord 실패 알림 + JSON 로깅 + .env.example
- Windows Task Scheduler 일일 자동 수집
- 데이터 신선도 체크 (자산별 최신일 vs T-1 비교)

## 5. Task Breakdown

→ `phase2-collector-tasks.md` 참조

## 6. Risks & Mitigation

| 리스크 | 영향 | 완화 |
|--------|------|------|
| FDR 3년 데이터 요청 시 타임아웃 | 백필 실패 | 연도별 chunk 분할 수집 |
| Railway DB 무료 플랜 용량 한계 | 저장 실패 | 7자산 × 750일 = ~5,250행 (미미) |
| BTC/KRW 3년 데이터 불완전 | 결측 | BTC/USD fallback 자동 전환 |
| 영업일 캘린더 자산별 차이 | 갭 오탐 | 자산 category별 캘린더 분리 (crypto=매일) |

## 7. Dependencies

- Railway PostgreSQL 가동 중 (Phase 1에서 확인 완료)
- `backend/.env`에 `DATABASE_URL` 설정 완료
- `asset_master` 7개 자산 seeded (Phase 1.5)
- FDR 패키지 설치 완료 (`finance-datareader`)
