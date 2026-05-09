# Lessons Learned — Stock Dashboard

> Generated: 2026-04-10
> Source: Phase 5~7, A~G debug-history.md + 성능 최적화 PERF-1
> 역할: **사후 회고표가 아니라, 유사 프로젝트를 위한 실수 방지 플레이북**

---

## High-Impact 교훈 (상세)

### T-003: 요청 스코프 DB 세션을 백그라운드 태스크에 전달하면 세션 닫힘 후 실패

- **문제**: `asyncio.ensure_future()`에 FastAPI 요청 스코프 DB 세션을 넘기면, 요청 종료 시 세션이 닫혀 백그라운드 태스크가 실패
- **왜 발생했는가**: FastAPI의 `Depends(get_db)` 세션은 요청 라이프사이클에 바인딩. 요청 완료 후 `finally`에서 `close()` 호출
- **조기 징후**: 백그라운드 태스크에서 간헐적 `SessionClosedError` 또는 "instance is not bound to a Session" 에러. 요청 응답은 정상(200 OK)인데 DB에 데이터 미저장
- **예방 규칙**: **백그라운드 태스크는 반드시 자체 `SessionLocal()` 생성 + `try/finally close`**. 요청 스코프 세션을 절대 전달하지 말 것
- **코드/설계 대응**: `SessionLocal()` 직접 생성, `try/finally` 패턴으로 세션 라이프사이클 관리
- **PR 전 점검법**: `asyncio.ensure_future`, `create_task`, `BackgroundTasks.add_task` 호출부에서 `db` 파라미터가 DI 세션인지 확인
- **관련 pattern**: `fastapi-dependency-injection.py`
- **관련 blueprint 단계**: Phase G

### T-005: `order_by(asc) + limit=N` 함정 — "가장 오래된 N개"가 반환됨

- **문제**: 시계열 repo가 `asc` 정렬 고정일 때, `limit=N`은 가장 오래된 N개를 반환. 최신 데이터가 필요한 곳에서 3년 전 데이터 사용
- **왜 발생했는가**: 정렬 방향을 함수 호출부에서 확인하지 않고 limit만 추가
- **조기 징후**: 차트나 분석 결과가 "과거 데이터"만 보여줌. 금액/수익률이 현재와 동떨어진 값
- **예방 ��칙**: **신규 조회 함수 추가 시 "이 limit은 어느 쪽 끝에서 자르는가?" 반드시 확인. desc 정렬 전용 함수 또는 date 필터로 범위 한정**
- **코드/��계 대응**: `get_latest_N()` 같은 desc 정렬 전용 함수 분리. 기존 호출부 grep 전수조사
- **PR 전 점검법**: `limit=` 패턴을 grep → 각 호출부의 정렬 방향 확인
- **관련 pattern**: 없음
- **관련 blueprint 단계**: Phase 4 (REST API)

### T-009: OpenAI 529 에러를 "서버 문제"로 단정하면 근본 원인을 놓침

- **문제**: 529 에러 발생 시 "OpenAI 서버 과부하"로 단정 → timeout 늘리기만 반복 → 실제 원인(토큰 누적, 재시도 과다)을 놓침
- **왜 발생했는가**: 외부 원인을 먼저 의심하는 습관. 내부 코드 변경 가능성을 후순위로 둠
- **조기 징후**: 동일 질문이 어제는 되고 오늘은 안 됨. timeout 값을 올려도 개선 없음. `GET /models` API는 정상 응답
- **예방 규칙**: **API 에러 시 3단계 진단: (1) 간단한 API 호출로 서버 정상 확인 (2) 요청 크기/토큰 수 확인 (3) 재시도 로직 확인. 외부 원인 단정 금지**
- **코드/설계 대응**: `max_retries=3`, `request_timeout=10` 명시. 요청 토큰 수 로깅
- **PR 전 점검법**: LLM 호출부에 timeout/retries 명시 여부 확인
- **관련 pattern**: `langraph-classifier.py`
- **관련 blueprint 단계**: Phase F

### T-010: LangChain `with_structured_output` 프로덕션에서 지속 실패

- **문제**: `with_structured_output(Pydantic)` 간헐적 파싱 실패 → 재시도 → 토큰 폭발
- **왜 발생���는가**: LangChain 고수준 추상화가 LLM 응답 형식 변동에 취약
- **조기 징후**: 동일 프롬프트에서 간헐적 파싱 에러. 재시도 횟수 증가. 토큰 비용 급등
- **예방 규칙**: **`with_structured_output` 대신 `response_format=json_object` + 수동 `json.loads` + Pydantic 파싱 사용. LangChain 고수준 추상화보다 저수준 직접 제어 선호**
- **코드/설계 대응**: JSON Mode + 수동 파싱 + fallback 체인
- **PR �� 점검법**: `with_structured_output` 사용 여부 grep. 있으면 JSON Mode로 전환 검토
- **관련 pattern**: `langraph-classifier.py`
- **관련 blueprint 단계**: Phase F

### T-023: reasoning 모델은 temperature/max_tokens 미지원 — "느려짐"으로 발현

- **문제**: gpt-5-mini/nano에 `temperature=0` 전달 → 400 에러 → LangChain 자동 재시도 → 25초+ 소요. 에러가 아닌 "느려짐"으로 나타남
- **왜 발생했는가**: reasoning 모델과 non-reasoning 모델의 파라미터 호환성 차이를 몰랐음
- **조기 징후**: 특정 모델로 교체 후 응답 시간 급등. 에러 로그 없이 느려짐만 관찰됨
- **예방 규칙**: **새 모델 도입 시 반드시 reasoning/non-reasoning 여부 확인. reasoning 모델은 `temperature`, `max_tokens` 대신 `max_completion_tokens` 사용. JSON 리포트 같은 단순 작업엔 non-reasoning이 4-7배 빠름**
- **코드/설계 대응**: Reporter를 `gpt-4.1-mini`(non-reasoning)로 분리. 모델별 파라미터 분기
- **PR 전 점검법**: LLM 초기화 코드에서 모델명 확인 → reasoning 모델이면 temperature/max_tokens 사용 여부 점검
- **관련 pattern**: 없음
- **관련 blueprint 단계**: Phase F

### T-024: 인메모리 캐시는 서버 재시작마다 소멸 — Cache Warmup 필수

- **문제**: DataFetcher의 인메모리 캐시가 서버 재시작 시 소멸 → 첫 요청 항상 cold (12s)
- **왜 발생했는가**: 인메모리 캐시의 근본적 한계를 간과
- **조기 징후**: 배포/재시작 직후 첫 사용자 요청이 유독 느림. 이후 요청은 정상
- **예방 규칙**: **인메모리 캐시를 쓰는 서비스는 반드시 Cache Warmup(서버 시작 시 프리페치) 고려. lifespan hook + asyncio.create_task 패턴**
- **코드/설계 대응**: `cache_warmup.py` — lifespan hook에서 29개 tool 결과 백그라운드 프리페치 (17s). cold 12s → ~1.3s
- **PR 전 점검법**: 인메모리 캐시 도입 시 "서버 재시작 후 첫 요청" 시나리오 테스트 여부 확인
- **관련 pattern**: 없음
- **관련 blueprint 단계**: Phase F

### A-004: 대시보드 데이터 소스와 Agentic 데이터 소스를 1:1 매칭하지 않으면 불일치 응답

- **문제**: 대시보드 API와 Agentic LLM 툴이 서로 다른 함수/쿼리를 사용 → 동일 질문에 다른 수치 응답
- **왜 발생했는가**: AI 기능 확장 시 기존 대시보드 API 함수를 재사용하지 않고 별도 구현
- **조기 징후**: 대시보드에서 보이는 수치와 AI 채팅 응답 수치가 다름
- **예방 규칙**: **Agentic Flow의 데이터 조회 함수는 반드시 대시보드 API와 동일한 소스 사용. 새 분석 함수 추가 시 LLM 툴도 동시 업데이트**
- **코드/설계 대응**: 공통 서비스 레이어에서 데이터 조회, API와 LLM 툴이 같은 서비스 호출
- **PR 전 점검법**: 새 API 엔드포인트 추가 시 대응하는 LLM 툴 존재 여부 확인
- **관련 pattern**: 없음
- **관련 blueprint 단계**: Phase F, G

---

## 기술적 교훈 (Technical) — 일반 항목

| ID | 카테고리 | 문제 | 해결 | 예방 규칙 | Phase |
|----|----------|------|------|----------|-------|
| T-001 | db | PostgreSQL `jsonb_set` nested path — 중간 키 없으면 실패 | 상위 키 `'{}'::jsonb` 보장 2-step 접근 | JSONB 중첩 업데이트 시 상위 경로 존재 확인 먼저 | G |
| T-002 | db | `json` 컬럼에 `jsonb_set` 결과 타입 불일치 | `::json` 캐스트 추가 | json/jsonb 혼용 금지. 컬럼 타입 통일 또는 캐스트 명시 | G |
| T-004 | db | `try/except`에서 DB 쓰기 에러 무시 → 200 OK + 데이터 미저장 | 에러 전파 + 로깅 강화 | DB 쓰기 에러는 절대 삼키지 말 것. 에러 전파 필수 | G |
| T-006 | data | pandas/numpy NaN이 DB에 그대로 저장됨 | API 스키마 레벨에서 방어적 변환 | 수치 데이터 DB 적재 전 NaN/Inf 체크 필수 | 5 |
| T-007 | data | `numpy.float64`/`Timestamp` → SQLAlchemy 실패 | Python native 타입 변환 | pandas→DB 적재 시 `.item()`, `.to_pydatetime()` 변환 | 5 |
| T-008 | data | `compute_all_factors()`는 파생 팩터만 반환 | 원시 OHLCV 컬럼 별도 합침 | 팩터 함수의 반환 컬럼 목록 문서화. 필요 컬럼 누락 체크 | 5 |
| T-011 | ai | LangChain 0.3→1.x `on_tool_end` 반환 타입 변경 | 반환 타입 확인 후 수정 | 메이저 업그레이드 시 콜백 반환 타입 breaking change 확인 | B |
| T-012 | ai | LLM 기본 재시도가 과도 → 토큰 폭발 | `max_retries=3`, `request_timeout=10` 명시 | 모든 LLM 호출에 timeout+retries 명시. 기본값 신뢰 금지 | F |
| T-013 | ai | Agentic 단일 턴 LLM — 대화 맥락 없음 | 최근 N턴 user_msg에 요약 포함 | 멀티턴 AI 기능은 히스토리 전달 설계를 초기에 결정 | G |
| T-014 | frontend | SSE `fetch`는 axios 인터셉터 범위 밖 → 401 미처리 | `sendMessageSSE` 내 별도 401 감지 + refresh + 재시도 | SSE/WebSocket 사용 시 인증 갱신 로직을 별도 구현 | G |
| T-015 | frontend | `tsc --noEmit` 통과하지만 `tsc -b`(Vercel)는 더 엄격 | 로컬에서 `tsc -b`도 확인 | CI/배포 빌드 명령과 로컬 검증 명령을 일치시킬 것 | E |
| T-016 | infra | Windows uvicorn `--reload` 파일 변경 감지 실패 + 좀비 프로세스 | `tasklist` → `taskkill` 전부 → 재시작 | Windows에서 uvicorn --reload 신뢰 금지. 수동 재시작 습관 | 5, G |
| T-017 | infra | Vite 포트 충돌 시 자동으로 다음 포트 사용 | CORS에 연속 포트 미리 등록 | CORS 설정 시 개발 포트 범위(5173-5175) 허용 또는 regex | 5 |
| T-018 | infra | Railway `postgres://` → SQLAlchemy 2.x `postgresql://`만 | 앱 코드에서 자동 변환 | DB URL 스키마 자동 변환 유틸 포함. 수동 설정 의존 금지 | 6 |
| T-019 | infra | Railway `startCommand`는 셸 없이 실행 → 변수 확장 안 됨 | `sh -c '...'`로 래핑 | PaaS startCommand는 항상 `sh -c` 래핑 여부 확인 | 6 |
| T-020 | infra | 환경변수 3종 미설정 시 앱 미동작 | 배포 체크리스트 | 배포 전 필수 환경변수 체크리스트 작성. 코드로 검증 가능하면 startup 시 체크 | 6 |
| T-021 | infra | CORS origin trailing `/` → exact match 실패 | `.rstrip("/")` 처리 | CORS origin 설정 시 trailing slash 자동 제거 로직 포함 | 6 |
| T-022 | infra | GitHub Push Protection — 문서에 API 키 포함 시 push 거부 | 문서에 비밀값 포함 금지 | 커밋 전 민감 정보 grep 습관. `.gitignore`에 `.env*` 포함 | B |

## 설계 교훈 (Architecture)

| ID | 카테고리 | 결정 | 이유 | 예방 규칙 | 결과 |
|----|----------|------|------|----------|------|
| A-001 | data | UX와 데이터 Flow 정합성 — Canonical Form 중앙 관리 | 페이지 간 파라미터 일관성 필수 | 변수명/파라미터를 Canonical Form으로 정의하고 전 계층에서 재사용 | Agentic Flow에도 동일 적용 |
| A-002 | data | 페이지 책임제 — 모든 변수를 Canonical Form으로 정의 | 대시보드+Agentic 일관 재사용 | 새 페이지/기능 추가 시 기존 Canonical Form 준수 여부 먼저 확인 | 종목/기간/시점 혼란 방지 |
| A-003 | ai | Agentic Flow 가시성 확보 — 노드/함수/재활용 범위 명시 | 복잡성 가시화가 문제 해결 출발점 | AI 파이프라인은 반드시 Flow 다이어그램 문서화. 노드 추가 시 업데이트 | Flow 문서로 디버깅 시간 단축 |
| A-005 | api | Router-Service-Repository 3계층 분리 | 테스트 용이성, 관심사 분리 | API 코드는 3계층 분리 강제. Router에 비즈니스 로직 금지 | 874개 테스트 달성 |
| A-006 | auth | JWT + Refresh Token Rotation | 외부 서비스 의존 없이 완전 제어 | 인증 자체 구현 시 Refresh Rotation 필수. 단순 Access Token만은 위험 | passlib→bcrypt 직접 사용 |
| A-007 | ai | 하이브리드 분류 (정규표현식 + LLM fallback) | 레이턴시 최소화 + 안전 | 분류 작업은 규칙 기반 먼저, LLM은 fallback으로만 | Classifier 2초 내 응답 |
| A-008 | ai | 2-Step LLM + 모델 분리 (reasoning/non-reasoning) | Reporter에 reasoning 불필요 → 6배 속도 개선 | LLM 파이프라인은 단계별 모델 요구사항 분석 후 모델 분리 | 34.8s→5.8s |
| A-009 | db | CASCADE FK로 사용자 삭제 시 관련 데이터 자동 정리 | 수동 삭제 로직 불필요 | 소유 관계(user→session→message)는 CASCADE FK 설계 | 회원 탈퇴 간소화 |
| A-010 | infra | Minimum Viable Deploy 전략 | 디버깅 변수 많을 때 최소 배포→점진 복원 | 배포 3회 이상 실패 시 모든 복잡성 제거→최소 상태로 재시도 | 5회 실패→1회 성공 |
| A-011 | ai | Cache Warmup으로 Cold Start 제거 | 인메모리 캐시 소멸 문제 우회 | 인메모리 캐시 사용 시 lifespan hook 프리페치 기본 고려 | Cold/Warm 모두 ~15s |

## 프로세스 교훈 (Process)

| ID | 카테고리 | 교훈 | 예방 규칙 | 상세 |
|----|----------|------|----------|------|
| P-001 | testing | 동일 근본 원인 버그는 전수조사 필수 | **버그 수정 시 grep으로 동일 패턴 전체 검색 → 안전/위험 분류 → 위험한 곳만 수정** | 1건 수정으로 끝내면 다른 위치에서 재발 |
| P-002 | testing | 로컬 서버 테스트 시 서버 환경 사전 확인 | 테스트 오류 시 서버 환경(프로세스, 포트, DB) → 코드 순서로 디버깅 | 코드부터 의심하면 시간 낭비 |
| P-003 | testing | 로깅 레벨 설정 사전 확인 | 테스트 시작 전 WARNING/DEBUG/INFO 설정 확인 | 로그 누락으로 디버깅 시간 증가 |
| P-004 | testing | 서버 추가 기동 → 여러 PID 공존 문제 | single server 유지되도록 테스트마다 기존 프로세스 확인 | 포트 충돌 또는 구버전 응답 |
| P-005 | testing | CLI 기반 백엔드 테스트 프레임워크 필요 | curl/httpie 기반 API 테스트 스크립트 초기 구축 | 브라우저 의존 테스트는 재현성 낮음 |
| P-006 | deploy | Railway 빌드/런타임 로그가 CI에 충분히 노출 안 됨 | PaaS 로그 접근 방법을 배포 전에 파악. CLI 로그 명령 제약 확인 | SPA 대시보드에서만 확인 가능한 정보 존재 |
| P-007 | deploy | nixpacks 빌드 불안정 — 로그 없이 실패 가능 | **Dockerfile 기반이 더 안정적. nixpacks는 프로토타입에만** | 프로덕션 빌드는 제어 가능한 도구 사용 |
| P-008 | ai | LLM API 키 무료 티어 한도 미리 확인 | AI 기능 시작 전 결제 설정 + 쿼타 확인 | 429 에러로 개발 블로킹 |
| P-009 | data | LLM 출력을 tool에 전달 전 validation | **외부 입력(LLM 출력 포함)은 tool 함수 진입 전 반드시 검증** | correlation tool에 자산 1개 전달 시 ValueError |
