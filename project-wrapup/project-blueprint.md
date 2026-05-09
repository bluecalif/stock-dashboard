# Project Blueprint — 데이터 수집/분석/시각화 + AI 채팅 대시보드 설계 가이드

> Source: Stock Dashboard (2026-02 ~ 2026-03) 개발 경험 기반
> 역할: **단순 Phase 목록이 아니라, 유사 프로젝트를 위한 이상적 개발 계획서**

## 프로젝트 유형

금융/데이터 자산의 **수집 → 저장 → 분석 → 시각화 → AI 상담** 파이프라인을 갖춘 풀스택 대시보드.
시계열 데이터, 팩터/지표 분석, 전략 백테스트, Agentic AI 채팅을 포함.

---

## 의사결정 규칙

이 규칙은 모든 Phase에서 적용되며, 위반 시 후반부에서 대규모 재작업이 발생한다.

1. **배포와 데이터 정합성 전에 AI 확장을 먼저 하지 않는다**
2. **Canonical Form과 데이터 Flow 정합성을 먼저 고정한다** — A-001, A-002
3. **대시보드와 Agentic 데이터 소스 일치 전에는 AI 고도화를 확장하지 않는다** — A-004
4. **실사용 근거가 없는 Context/Memory는 후순위로 둔다**
5. **배포 3회 이상 실패 시 Minimum Viable Deploy 전략 적용** — A-010

---

## 권장 개발 경로

### Core Path (반드시 먼저 — Phase 1~7)

#### Phase 1: Skeleton + DB
- **목표**: 프로젝트 구조, DB 스키마, 마이그레이션
- **선행조건**: 없음 (첫 번째 Phase)
- **완료조건**: `alembic upgrade head` 성공, 테이블 생성 확인
- **시작하지 말아야 할 조건**: API 엔드포인트, 프론트엔드 페이지
- **초기에 결정할 사항**: `ondelete="CASCADE"` FK 설정, UUID vs 정수 PK, JSONB 사용 여부
- **관련 교훈**: A-009
- **규모감**: 소 (1~2일)

#### Phase 2: Data Collector
- **목표**: 외부 데이터 소스 연동, 정합성 검증, Idempotent UPSERT
- **선행조건**: Phase 1 완료 (DB 테이블 존재)
- **완료조건**: 전 자산 1년 데이터 수집 + DB 적재 성공
- **시작하지 말아야 할 조건**: 분석 로직, API
- **초기에 결정할 사항**: 데이터 소스 우선순위, 재시도/알림 로직
- **관련 교훈**: T-006, T-007
- **규모감**: 중 (2~3일)

#### Phase 3: Analysis Engine
- **목표**: 팩터 생성, 전략 신호, 백테스트, 성과 지표
- **선행조건**: Phase 2 완료 (DB에 원시 데이터 존재)
- **완료조건**: 전략 3종 백테스트 성공 + 성과 메트릭 계산
- **시작하지 말아야 할 조건**: API 엔드포인트, 차트 시각화
- **초기에 결정할 사항**: Strategy ABC 패턴, 팩터 DF 컬럼 구성(원시+파생)
- **관련 교훈**: T-008
- **규모감**: 중 (3~5일)

#### Phase 4: REST API
- **목표**: FastAPI CRUD + 분석 엔드포인트
- **선행조건**: Phase 3 완료 (분석 결과 DB에 존재)
- **완료조건**: 모든 엔드포인트 Swagger 테스트 성공
- **시작하지 말아야 할 조건**: 프론트엔드 (API가 안정되어야 프론트 시작)
- **초기에 결정할 사항**: Router-Service-Repository 3계층 분리, Pydantic 스키마, `order_by` 방향 규칙
- **관련 교훈**: A-005, T-005
- **규모감**: 중 (2~3일)

#### Phase 5: Frontend Dashboard
- **목표**: React 시각화 페이지 (가격, 상관, 팩터, 전략)
- **선행조건**: Phase 4 완료 (API 엔드포인트 안정)
- **완료조건**: 전 페이지 브라우저 렌더 성공
- **시작하지 말아야 할 조건**: AI 기능, 인증
- **초기에 결정할 사항**: Canonical Form 변수 정의, 차트 라이브러리 선택, 상태 관리 패턴
- **관련 교훈**: A-001, A-002, T-017
- **규모감**: 중 (3~5일)

#### Phase 6: Deploy & Ops
- **목표**: CI/CD, 프로덕션 배포, 헬스체크
- **선행조건**: Phase 5 완료 (전 기능 로컬 동작 확인)
- **완료조건**: 프로덕션 URL에서 전 기능 동작
- **시작하지 말아야 할 조건**: 고급 기능 (먼저 코어를 프로덕션에 안착시킬 것)
- **초기에 결정할 사항**: Dockerfile vs nixpacks, 환경변수 체크리스트, startCommand 래핑
- **관련 교훈**: T-018, T-019, T-020, T-021, A-010, P-007
- **규모감**: 중 (2~3일)

#### Phase 7: Scheduled Collection
- **목표**: 정기 데이터 수집 (GitHub Actions cron 등)
- **선행조건**: Phase 6 완료 (프로덕션 배포 성공)
- **완료조건**: 일일 수집 자동 실행 + 실패 알림
- **시작하지 말아야 할 조건**: AI 기능 확장
- **초기에 결정할 사항**: UTC 시간대 변환, 스케줄러 종류
- **관련 교훈**: 없음
- **규모감**: 소 (1~2일)

---

### Expansion Path (Core 완료 후 — Phase A~G)

#### Phase A: Authentication
- **목표**: JWT 인증 (회원가입/로그인/갱신/탈퇴)
- **선행조건**: Phase 6 완료 (배포 환경 안정). Core Path 전체 완료
- **완료조건**: 인증 플로우 E2E 테스트 성공
- **시작하지 말아야 할 조건**: AI 채팅 (인증 완료 후에 사용자 식별 가능)
- **초기에 결정할 사항**: Refresh Token Rotation, 선택적 인증, CASCADE FK
- **관련 교훈**: A-006, A-009
- **규모감**: 중 (2~3일)

#### Phase B: AI Chatbot
- **목표**: LLM 기반 채팅 (SSE 스트리밍)
- **선행조건**: Phase A 완료 (사용자 식별 가능)
- **완료조건**: 질문 → 분석 응답 E2E 성공
- **시작하지 말아야 할 조건**: Agentic Flow, 복잡한 분류기 (단순 채팅부터)
- **초기에 결정할 사항**: LLM API 키 쿼타 확인, LangChain 버전 호환성, SSE vs WebSocket
- **관련 교훈**: T-011, T-022, P-008
- **규모감**: 중 (3~5일)

#### Phase C~D: 분석 페이지 고도화
- **목표**: 상관 분석, 지표 시각화, 피드백 반영
- **선행조건**: Phase 5 완료 (기본 대시보드 존재)
- **완료조건**: 대시보드 전 페이지 정합성 확인
- **시작하지 말아야 할 조건**: Agentic AI (대시보드 데이터가 먼저 안정되어야)
- **초기에 결정할 사항**: 페이지 책임제 Canonical Form, UX 시나리오 전수 검토
- **관련 교훈**: A-001, A-002
- **규모감**: 대 (5~7일)

#### Phase E: Strategy Visualization
- **목표**: 전략 성과 페이지, 에쿼티 커브, 거래 내역
- **선행조건**: Phase C~D 완료 (분석 데이터 정합성 확인)
- **완료조건**: 전략 비교 차트 렌더 성공
- **시작하지 말아야 할 조건**: Agentic AI
- **초기에 결정할 사항**: `tsc -b` 로컬 빌드 검증
- **관련 교훈**: T-015
- **규모감**: 중 (3~4일)

#### Phase F: Agentic AI
- **목표**: 2-Step LLM (분류기 + 리포터), 자동 데이터 조회
- **선행조건**: Phase E 완료 + **대시보드와 동일한 데이터 소스 준비 (A-004 필수)**
- **완료조건**: 질문 → 분류 → 데이터 조회 → 분석 응답 E2E
- **시작하지 말아야 할 조건**: Context/Memory (Agentic Flow가 먼저 안정되어야)
- **초기에 결정할 사항**: JSON Mode(T-010), max_retries+timeout(T-012), reasoning/non-reasoning 모델 분리(T-023), Cache Warmup(T-024)
- **관련 교훈**: T-009, T-010, T-012, T-023, T-024, A-003, A-004, A-007, A-008, A-011, P-009
- **규모감**: 대 (4~6일)

#### Phase G: Context & Memory
- **목표**: 사용자 프로필, 대화 메모리, 히스토리 전달
- **선행조건**: Phase F 완료 (Agentic Flow 안정). **실사용 데이터로 Context 필요성 확인 후에만 시작**
- **완료조건**: 프로필 기반 응답 톤 차이 + 이전 대화 참조 가능
- **시작하지 말아야 할 조건**: 없음 (최종 단계)
- **초기에 결정할 사항**: 백그라운드 태스크 DB 세션 분리(T-003), 토큰 절약 위해 히스토리 요약
- **관련 교훈**: T-001, T-002, T-003, T-004, T-005, T-013, T-014
- **규모감**: 대 (4~6일)

---

## 피해야 할 함정

| # | 함정 | 왜 위험한가 | 대안 | 관련 교훈 |
|---|------|------------|------|----------|
| 1 | `order_by(asc) + limit=N`으로 최신 데이터 조회 | 가장 오래된 N개가 반환됨 | desc 정렬 전용 함수 또는 date 필터 | T-005 |
| 2 | 요청 스코프 DB 세션을 백그라운드 태스크에 전달 | 요청 종료 시 세션 닫힘 → 태스크 실패 | 자체 `SessionLocal()` 생성 | T-003 |
| 3 | LangChain `with_structured_output` 프로덕션 사용 | 간헐적 파싱 실패 → 토큰 폭발 | JSON Mode + 수동 파싱 | T-010 |
| 4 | OpenAI 529 에러를 서버 문제로 단정 | 토큰 누적/재시도 과다가 원인일 수 있음 | 3단계 진단 (서버→요청크기→재��도) | T-009 |
| 5 | LLM 기본 retry 설정 사용 | 토큰 비용 폭발 | `max_retries=3`, `request_timeout=10` 명시 | T-012 |
| 6 | Windows uvicorn `--reload` 신뢰 | 좀비 프로세스 잔류, 코드 미반영 | 수동 프로세스 kill + 재시작 | T-016 |
| 7 | try/except에서 DB 에러 무시 | 200 OK + 데이터 미저장 → 디버깅 난항 | 에러 전파 + 로깅 | T-004 |
| 8 | nixpacks 빌드 사용 | 로그 없이 실패 가능 | Dockerfile 기반 | P-007 |
| 9 | 환경변수 설정 누락 | 코드 완벽해도 앱 미동작 | 배포 체크리스트 | T-020 |
| 10 | SSE에서 axios 인터셉터 의존 | fetch API는 범위 밖 → 401 미처리 | 별도 401 감지 로직 | T-014 |
| 11 | 동일 근본 원인 버그 1건만 수정 | 다른 위치에서 같은 버그 반복 | grep 전수조사 | P-001 |
| 12 | 대시보드 데이터 소스 ≠ Agentic 데이터 소스 | 사용자에게 불일치 응답 | 내부 함수 1:1 매칭 | A-004 |

---

## 추천 스택 조합

### 검증된 조합 (이 프로젝트)
| 영역 | 기술 | 선택 이유 |
|------|------|----------|
| Backend | FastAPI + SQLAlchemy 2.0 | 타입 힌팅, DI, Pydantic 통합 |
| DB | PostgreSQL (Railway) | JSONB, UPSERT, CASCADE FK |
| Data | pandas + numpy | 시계열 분석 표준 |
| Frontend | React + Recharts + Zustand | 차트 다양성, 상태 관리 간결 |
| Styling | TailwindCSS | 빠른 UI 구성, 커스텀 용이 |
| AI | LangGraph + OpenAI | 명시적 그래프, SSE 지원 |
| Auth | JWT (python-jose + bcrypt) | 외부 의존 없이 완전 제어 |
| Deploy | Railway + Vercel + GitHub Actions | 각 영역 최적화된 저가 플랫폼 |

### 대안
| 영역 | 대안 | 트레이드오프 |
|------|------|------------|
| Backend | Django REST Framework | 더 많은 내장 기능, 더 무거움 |
| DB | Supabase (PostgreSQL) | Auth 내장, 무료 티어 제한 |
| Frontend | Next.js | SSR 지원, 더 복잡 |
| AI | CrewAI, AutoGen | 멀티 에이전트, 더 복잡한 설정 |
| Auth | Supabase Auth, Auth0 | 관리 편의, 외부 의존 |

---

## 체크리스트

### Phase 완료 시 확인
- [ ] 모든 테스트 통과 (`pytest`, `tsc -b`)
- [ ] Lint clean (`ruff check .`)
- [ ] 브라우저 E2E 확인 (해당 페이지)
- [ ] debug-history.md 업데이트
- [ ] session-compact.md TODO 갱신

### 배포 전 확인
- [ ] 환경변수 3종 설정 (DATABASE_URL, CORS_ORIGINS, VITE_API_BASE_URL)
- [ ] 헬스체크 엔드포인트 동작
- [ ] CORS trailing slash 처리 — T-021
- [ ] `postgres://` → `postgresql://` 변환 — T-018
- [ ] startCommand `sh -c` 래핑 — T-019

### AI 기능 확인
- [ ] LLM API 키 유효 + 결제 설정 — P-008
- [ ] `max_retries`, `request_timeout` 명시 — T-012
- [ ] reasoning/non-reasoning 모델 구분 — T-023
- [ ] 분류기 fallback 동작 — A-007
- [ ] 대시보드 ↔ Agentic 데이터 소스 일치 — A-004
- [ ] SSE 401 처리 로직 — T-014
- [ ] Cache warmup 동작 확인 — T-024
