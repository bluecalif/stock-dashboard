# Phase F: Full Agentic Flow — Debug History
> Last Updated: 2026-03-18

## Step F.1: Pydantic 스키마 정의

| Bug # | Page/Module | Issue | Fix | File |
|-------|-------------|-------|-----|------|
| (구현 시 기록) | | | | |

## Step F.2: Knowledge Expert Prompts

| Bug # | Page/Module | Issue | Fix | File |
|-------|-------------|-------|-----|------|
| (구현 시 기록) | | | | |

## Step F.3: LLM Classifier

| Bug # | Page/Module | Issue | Fix | File |
|-------|-------------|-------|-----|------|
| (구현 시 기록) | | | | |

## Step F.4: DataFetcher

| Bug # | Page/Module | Issue | Fix | File |
|-------|-------------|-------|-----|------|
| (구현 시 기록) | | | | |

## Step F.5: LLM Reporter

| Bug # | Page/Module | Issue | Fix | File |
|-------|-------------|-------|-----|------|
| (구현 시 기록) | | | | |

## Step F.6: chat_service.py 통합

| Bug # | Page/Module | Issue | Fix | File |
|-------|-------------|-------|-----|------|
| (구현 시 기록) | | | | |

## Step F.7: follow_up SSE + 프론트엔드

| Bug # | Page/Module | Issue | Fix | File |
|-------|-------------|-------|-----|------|
| (구현 시 기록) | | | | |

## Step F.8: Navigate 핸들러

| Bug # | Page/Module | Issue | Fix | File |
|-------|-------------|-------|-----|------|
| (구현 시 기록) | | | | |

## Step F.9: 레거시 정리

| Bug # | Page/Module | Issue | Fix | File |
|-------|-------------|-------|-----|------|
| (구현 시 기록) | | | | |

## Step F.10: 통합 검증 (E2E 프로덕션 테스트)

| Bug # | Page/Module | Issue | Fix | File |
|-------|-------------|-------|-----|------|
| F.10-1 | chat_service | `_default_follow_ups` 함수 미정의 → NameError | 함수 추가 필요 | `chat_service.py:210` |
| F.10-2 | chat_service | Agentic flow 미작동 → LangGraph fallback만 실행 | 아래 심층 분석 참조 | `chat_service.py`, `graph.py` |
| F.10-3 | correlation | highlight_pair 시각적 효과 미반영 | 히트맵 컴포넌트에서 highlightedPair 소비 로직 필요 | 프론트엔드 |
| F.10-4 | chat_service | 529 overloaded_error 반복 (attempt 9/10) | 아래 심층 분석 참조 | `classifier.py`, `graph.py`, `reporter.py` |

### F.10-4: 529 Overloaded Error — 심층 분석

**증상:**
- OpenAI API 호출 시 `529 overloaded_error` 반복 발생
- LangChain 기본 재시도 로직이 최대 10회까지 시도 → 사용자 대기 시간 급증 (25초+ 간격)
- 직접 API key 테스트 시 200 OK → 서버 자체는 정상

**초기 오진:**
- "일시적 서버 과부하"로 판단 → 코드 수정 불필요하다고 결론
- ❌ **이 판단이 틀렸음** — 프로젝트 진행에 치명적 지연 초래

**실제 근본 원인 (추정):**
1. **MemorySaver 토큰 누적**: `graph.py:81`의 `MemorySaver()`가 session별 전체 대화 이력을 메모리에 보관 → `agent_node`에서 `model.ainvoke(messages)` 호출 시 모든 이전 메시지를 포함 → 긴 세션에서 토큰 폭발 → OpenAI 요청 크기 과다 → 529/rate limit
2. **재시도 로직 부재**: `ChatOpenAI`의 기본 `max_retries` 설정이 과도 → 실패 시 최대 10회 × 25초 = 250초 대기
3. **Classifier/Reporter도 무방비**: `classifier.py`, `reporter.py` 모두 `ChatOpenAI` 생성 시 `max_retries`, `request_timeout` 미설정

**수정 방향:**
1. 모든 `ChatOpenAI` 인스턴스에 `max_retries=3`, `request_timeout=10` 설정
2. LangGraph `agent_node`에서 메시지 이력 트리밍 (최근 N개만 유지)
3. 또는 세션 시작 시 이전 대화 이력 클리어 옵션 추가

**영향 파일:**
- `backend/api/services/llm/agentic/classifier.py`
- `backend/api/services/llm/agentic/reporter.py`
- `backend/api/services/llm/graph.py`
- `backend/api/services/chat/chat_service.py`

## Modified Files Summary
(Phase 전체 변경 파일 트리 — 구현 완료 후 기록)

## Lessons Learned

### L1: OpenAI 529 에러를 "일시적"으로 단정하지 말 것
- 529 = 반드시 서버 문제가 아님. 요청 토큰 크기 과다, 누적 메시지, rate limit 등 클라이언트 측 원인일 수 있음
- API key 직접 테스트(GET /models)로 서버 정상 확인 → 요청 payload 문제로 의심 전환
- **교훈**: API 에러 발생 시 "서버 문제"로 단정하기 전에 요청 크기, 토큰 수, 재시도 로직 먼저 확인

### L2: LLM 호출에 반드시 timeout + retry 제한 설정
- `ChatOpenAI()` 기본값이 과도한 재시도를 유발할 수 있음
- 모든 LLM 호출에 `max_retries=3`, `request_timeout=10` 명시적 설정 필수
- MemorySaver 사용 시 메시지 트리밍 로직 필수
