# Lessons Learned — Stock Dashboard

> Generated: 2026-03-21
> Source: Phase 5~7, A~G debug-history.md + core-critical-lessons.md

## 기술적 교훈 (Technical)

| # | 카테고리 | 문제 | 해결 | Phase |
|---|----------|------|------|-------|
| T-01 | db | PostgreSQL `jsonb_set` nested path 생성 불가 (중간 키 없으면 실패) | 상위 키를 `'{}'::jsonb`로 보장하는 2-step 접근 | G |
| T-02 | db | `json` 컬럼에 `jsonb_set` 결과 타입 불일치 | `::json` 캐스트 추가 | G |
| T-03 | db | 요청 스코프 DB 세션을 `asyncio.ensure_future`에 전달 → 세션 닫힘 후 실패 | 백그라운드 태스크는 자체 `SessionLocal()` 생성 + `try/finally` close | G |
| T-04 | db | `try/except`에서 DB 쓰기 에러 무시 → 200 OK + 데이터 미저장 | 에러 무시 금지, 로깅 강화 | G |
| T-05 | data | `order_by(asc) + limit=N`이 "가장 오래된 N개" 반환 — 최신 데이터 필요한 곳에서 오류 | `desc` 정렬 전용 함수 또는 `date` 필터로 범위 한정. 전수조사 필수 | G |
| T-06 | data | pandas/numpy NaN이 DB에 그대로 저장됨 | API 스키마 레벨에서 방어적 변환 필수 | 5 |
| T-07 | data | `numpy.float64`/`Timestamp` → SQLAlchemy `bulk_insert_mappings` 실패 | Python native 타입 변환 필수 | 5 |
| T-08 | data | `compute_all_factors()`는 파생 팩터만 반환 — 전략이 원시 OHLCV 필요 | 원시 컬럼을 별도로 합쳐서 전달 | 5 |
| T-09 | ai | OpenAI 529 에러를 "서버 문제"로 단정 → 토큰 누적/재시도 과다가 원인 | API 에러 시 요청 크기, 토큰 수, 재시도 로직 먼저 확인 | F |
| T-10 | ai | LangChain `with_structured_output(Pydantic)` 프로덕션 지속 실패 | `response_format=json_object` + 수동 `json.loads` + Pydantic 파싱 | F |
| T-11 | ai | LangChain 0.3→1.x 메이저 업그레이드 시 `on_tool_end` 반환 타입 변경 | 메이저 업그레이드 시 반환 타입 확인 필수 | B |
| T-12 | ai | LLM 기본 재시도가 과도 → 토큰 폭발 | `max_retries=3`, `request_timeout=10` 명시적 설정 | F |
| T-13 | ai | Agentic 단일 턴 LLM 호출 — 대화 맥락 없음 | 최근 N턴을 user_msg에 요약 포함 (토큰 절약) | G |
| T-14 | frontend | SSE `fetch`는 axios 인터셉터 범위 밖 → 401 갱신 안 됨 | `sendMessageSSE` 내 별도 401 감지 + refresh + 재시도 | G |
| T-15 | frontend | TypeScript `tsc --noEmit` 통과하지만 `tsc -b`(Vercel)는 더 엄격 | 로컬에서 `tsc -b`도 확인 | E |
| T-16 | infra | Windows uvicorn `--reload` 파일 변경 감지 실패 + 좀비 프로세스 | `tasklist`로 확인 → `taskkill` 전부 종료 → 재시작 | 5, G |
| T-17 | infra | Vite 포트 충돌 시 자동으로 다음 포트 사용 | CORS에 연속 포트 미리 등록 | 5 |
| T-18 | infra | Railway `postgres://` 스키마 — SQLAlchemy 2.x는 `postgresql://`만 지원 | 앱 코드에서 자동 변환 | 6 |
| T-19 | infra | Railway `startCommand`는 셸 없이 실행 — `${PORT:-8000}` 확장 안 됨 | `sh -c '...'`로 래핑 필수 | 6 |
| T-20 | infra | Railway 환경변수 3종(DB_URL, CORS, VITE_API) 미설정 시 앱 미동작 | 환경변수 = 배포의 마지막 마일 | 6 |
| T-21 | infra | CORS origin trailing `/` 포함 시 exact match 실패 | 코드에서 `.rstrip("/")` 처리 | 6 |
| T-22 | infra | GitHub Push Protection — 문서에 API 키 포함 시 push 거부 | 문서에 비밀값 포함 금지 | B |

## 설계 교훈 (Architecture)

| # | 카테고리 | 결정 | 이유 | 결과 |
|---|----------|------|------|------|
| A-01 | data | UX와 데이터 Flow 정합성 — 페이지 간/탭 간 데이터 중앙 관리 | 파라미터별 출력이 대시보드 전체에서 일관되어야 함 | Agentic Flow에도 동일 프레임워크 적용 |
| A-02 | data | 페이지 책임제 — 모든 변수를 Canonical Form으로 정의 | 대시보드 + Agentic Flow에서 일관 재사용 | 종목/기간/시점 혼란 방지 |
| A-03 | ai | Agentic Flow 가시성 확보 — 노드/함수/재활용 범위 명시 | 복잡성 가시화가 문제 해결 출발점 | README 등에 최신 Flow 업데이트 |
| A-04 | ai | 대시보드 데이터 Flow와 Agentic Flow 1:1 매칭 | 내부 함수도 동일 데이터 소스 사용해야 일관성 보장 | 새 분석 함수 추가 시 LLM 툴도 업데이트 |
| A-05 | api | Router-Service-Repository 3계층 분리 | 테스트 용이성, 관심사 분리 | 858+ 테스트 달성 |
| A-06 | auth | JWT + Refresh Token Rotation | 외부 서비스 의존 없이 완전 제어 | passlib 제거, bcrypt 직접 사용 |
| A-07 | ai | 하이브리드 분류 (정규표현식 + LLM fallback) | 레이턴시 최소화 + 안전 | Classifier 2초 내 응답 |
| A-08 | ai | 2-Step LLM (Classifier + Reporter) | LLM 최대 2회로 비용/레이턴시 최소화 | E2E 32초 (2+8+22) |
| A-09 | db | CASCADE FK로 사용자 삭제 시 관련 데이터 자동 정리 | 수동 삭제 로직 불필요 | 회원 탈퇴 구현 간소화 |
| A-10 | infra | Minimum Viable Deploy 전략 | 디버깅 변수 많을 때 모든 복잡성 제거 → 최소 배포 → 점진 복원 | 5회 실패 후 1회 만에 근본 원인 특정 |

## 프로세스 교훈 (Process)

| # | 카테고리 | 교훈 | 상세 |
|---|----------|------|------|
| P-01 | testing | 동일 근본 원인 버그는 전수조사 필수 | grep으로 패턴 전체 검색 → 안전/위험 분류 → 위험한 곳만 수정 |
| P-02 | testing | 로컬 서버 테스트 시 서버 환경 사전 확인 | 테스트 오류 시 서버 환경 → 코드 순서로 디버깅 |
| P-03 | testing | 로깅 레벨 설정 사전 확인 | WARNING/DEBUG/INFO 설정이 테스트 시작 전 올바른지 확인 |
| P-04 | testing | 서버 추가 기동 → 여러 PID 공존 문제 | single server 유지되도록 테스트마다 재확인 |
| P-05 | testing | 터미널 Bash로 백엔드 response 테스트하는 표준 프레임워크 필요 | 브라우저 테스트 외 CLI 테스트 자동화 |
| P-06 | deploy | Railway 빌드/런타임 로그가 CI에 충분히 노출 안 됨 | SPA 대시보드에서만 확인 가능한 정보 존재 → 디버깅 병목 |
| P-07 | deploy | nixpacks 빌드 불안정 — 로그 없이 실패 가능 | Dockerfile 기반이 더 안정적 |
| P-08 | ai | LLM API 키 무료 티어 한도 미리 확인 | 결제 설정 필수, 쿼타 초과 시 429 발생 |
| P-09 | data | correlation tool에 자산 개수 방어 | LLM 출력(외부 입력)을 tool에 전달 전 반드시 validation |
