# Project Blueprint — 데이터 수집/분석/시각화 + AI 채팅 대시보드 설계 순서도

> Source: Stock Dashboard (2026-02 ~ 2026-03) 개발 경험 기반

## 프로젝트 유형

금융/데이터 자산의 수집 → 저장 → 분석 → 시각화 → AI 상담 파이프라인을 갖춘 풀스택 대시보드.
시계열 데이터, 팩터/지표 분석, 전략 백테스트, Agentic AI 채팅을 포함.

---

## 권장 Phase 순서

### Phase 1: Skeleton + DB (1~2일)
- **목표**: 프로젝트 구조, DB 스키마, 마이그레이션
- **체크포인트**: `alembic upgrade head` 성공, 테이블 생성 확인
- **예상 규모**: 5~9 tasks
- **주의사항**: 스키마를 처음부터 확장 가능하게 설계. `ondelete="CASCADE"` FK 설정

### Phase 2: Data Collector (2~3일)
- **목표**: 외부 데이터 소스 연동, 정합성 검증, Idempotent UPSERT
- **체크포인트**: 전 자산 1년 데이터 수집 + DB 적재 성공
- **예상 규모**: 10 tasks
- **주의사항**: 단일 소스 의존 리스크 인식. 재시도/알림 로직 필수. numpy 타입 → Python native 변환

### Phase 3: Analysis Engine (3~5일)
- **목표**: 팩터 생성, 전략 신호, 백테스트, 성과 지표
- **체크포인트**: 전략 3종 백테스트 성공 + 성과 메트릭 계산
- **예상 규모**: 12 tasks
- **주의사항**: Strategy ABC 패턴으로 확장성 확보. 팩터 DF에 원시 컬럼 포함 여부 확인. NaN 방어

### Phase 4: REST API (2~3일)
- **목표**: FastAPI CRUD + 분석 엔드포인트
- **체크포인트**: 모든 엔드포인트 Swagger 테스트 성공
- **예상 규모**: 15 tasks
- **주의사항**: Router-Service-Repository 3계층 분리. Pydantic 스키마 정의. `order_by + limit` 방향 주의

### Phase 5: Frontend Dashboard (3~5일)
- **목표**: React 시각화 페이지 (가격, 상관, 팩터, 전략)
- **체크포인트**: 전 페이지 브라우저 렌더 성공
- **예상 규모**: 13 tasks
- **주의사항**: 차트 X축 정렬 방향. CORS 포트 설정. `Promise.allSettled` 방어 처리

### Phase 6: Deploy & Ops (2~3일)
- **목표**: CI/CD, 프로덕션 배포, 헬스체크
- **체크포인트**: 프로덕션 URL에서 전 기능 동작
- **예상 규모**: 9 tasks
- **주의사항**: **Minimum Viable Deploy 전략** 적용. Dockerfile 기반 권장 (nixpacks 불안정). 환경변수 체크리스트 필수. startCommand `sh -c` 래핑

### Phase 7: Scheduled Collection (1~2일)
- **목표**: 정기 데이터 수집 (GitHub Actions cron 등)
- **체크포인트**: 일일 수집 자동 실행 + 실패 알림
- **예상 규모**: 6 tasks
- **주의사항**: UTC 시간대 변환 주의

### Phase A: Authentication (2~3일)
- **목표**: JWT 인증 (회원가입/로그인/갱신/탈퇴)
- **체크포인트**: 인증 플로우 E2E 테스트 성공
- **예상 규모**: 16 tasks
- **주의사항**: Refresh Token Rotation. 선택적 인증(`get_current_user_optional`). CASCADE FK

### Phase B: AI Chatbot (3~5일)
- **목표**: LLM 기반 채팅 (SSE 스트리밍)
- **체크포인트**: 질문 → 분석 응답 E2E 성공
- **예상 규모**: 19 tasks
- **주의사항**: LLM API 키 쿼타 확인. LangChain 버전 호환성. SSE vs WebSocket 선택

### Phase C~D: 분석 페이지 고도화 (5~7일)
- **목표**: 상관 분석, 지표 시각화, 피드백 반영
- **체크포인트**: 대시보드 전 페이지 정합성 확인
- **예상 규모**: 50+ tasks
- **주의사항**: 페이지 책임제 — 변수 Canonical Form. UX 시나리오 전수 검토

### Phase E: Strategy Visualization (3~4일)
- **목표**: 전략 성과 페이지, 에쿼티 커브, 거래 내역
- **체크포인트**: 전략 비교 차트 렌더 성공
- **예상 규모**: 10 tasks
- **주의사항**: `tsc -b` (Vercel 빌드)도 로컬에서 확인

### Phase F: Agentic AI (4~6일)
- **목표**: 2-Step LLM (분류기 + 리포터), 자동 데이터 조회
- **체크포인트**: 질문 → 분류 → 데이터 조회 → 분석 응답 E2E
- **예상 규모**: 10 tasks
- **주의사항**: `with_structured_output` 대신 JSON Mode. `max_retries` + `request_timeout` 명시. LLM 출력 validation 필수

### Phase G: Context & Memory (4~6일)
- **목표**: 사용자 프로필, 대화 메모리, 히스토리 전달
- **체크포인트**: 프로필 기반 응답 톤 차이 + 이전 대화 참조 가능
- **예상 규모**: 20 tasks
- **주의사항**: 백그라운드 태스크 DB 세션 분리. 토큰 절약 위해 히스토리 요약

---

## 피해야 할 함정

| # | 함정 | 왜 위험한가 | 대안 |
|---|------|------------|------|
| 1 | `order_by(asc) + limit=N`으로 최신 데이터 조회 | 가장 오래된 N개가 반환됨. 3년 전 데이터 사용 | desc 정렬 전용 함수 또는 date 필터 |
| 2 | 요청 스코프 DB 세션을 백그라운드 태스크에 전달 | 요청 종료 시 세션 닫힘 → 태스크 실패 | 자체 `SessionLocal()` 생성 |
| 3 | LangChain `with_structured_output` 프로덕션 사용 | 간헐적 파싱 실패 | `response_format=json_object` + 수동 파싱 |
| 4 | OpenAI 529 에러를 서버 문제로 단정 | 토큰 누적/재시도 과다가 원인일 수 있음 | 요청 크기, 토큰 수 먼저 확인 |
| 5 | LLM 기본 retry 설정 사용 | 토큰 비용 폭발 | `max_retries=3`, `request_timeout=10` 명시 |
| 6 | Windows uvicorn `--reload` 신뢰 | 좀비 프로세스 잔류, 코드 미반영 | 수동 프로세스 kill + 재시작 |
| 7 | try/except에서 DB 에러 무시 | 200 OK + 데이터 미저장 → 디버깅 난항 | 에러 전파 + 로깅 |
| 8 | nixpacks 빌드 사용 | 로그 없이 실패 가능 | Dockerfile 기반 |
| 9 | 환경변수 설정 누락 | 코드 완벽해도 앱 미동작 | 배포 체크리스트 |
| 10 | SSE에서 axios 인터셉터 의존 | fetch API는 범위 밖 → 401 미처리 | 별도 401 감지 로직 |
| 11 | 동일 근본 원인 버그 1건만 수정 | 다른 위치에서 같은 버그 반복 | grep 전수조사 |
| 12 | 대시보드 데이터 소스 ≠ Agentic 데이터 소스 | 사용자에게 불일치 응답 | 내부 함수 1:1 매칭 |

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
| Deploy | Railway + Vercel + GitHub Actions | 각 영역 최적화된 무료/저가 플랫폼 |

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
- [ ] CORS trailing slash 처리
- [ ] `postgres://` → `postgresql://` 변환
- [ ] startCommand `sh -c` 래핑

### AI 기능 확인
- [ ] LLM API 키 유효 + 결제 설정
- [ ] `max_retries`, `request_timeout` 명시
- [ ] 분류기 fallback 동작
- [ ] 대시보드 ↔ Agentic 데이터 소스 일치
- [ ] SSE 401 처리 로직
