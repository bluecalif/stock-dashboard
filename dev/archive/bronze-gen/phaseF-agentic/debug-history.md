# Phase F: Full Agentic Flow — Debug History
> Last Updated: 2026-03-22

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
| F.3-1 | classifier | `with_structured_output(Pydantic)` 프로덕션 OpenAI API에서 지속 실패 | `response_format=json_object` + 수동 JSON 파싱으로 전환 | `classifier.py` |

## Step F.4: DataFetcher

| Bug # | Page/Module | Issue | Fix | File |
|-------|-------------|-------|-----|------|
| F.4-1 | data_fetcher | `asset_ids` 1개일 때 `compute_correlation`에서 `ValueError: At least 2 assets required` | `asset_ids<2`이면 `None` 전달 → 전체 활성 자산 사용 | `data_fetcher.py` |

## Step F.5: LLM Reporter

| Bug # | Page/Module | Issue | Fix | File |
|-------|-------------|-------|-----|------|
| F.5-1 | reporter | `with_structured_output(Pydantic)` 프로덕션에서 실패 (F.3-1과 동일) | `response_format=json_object` + 수동 파싱 전환 | `reporter.py` |

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

### F.10-5: DataFetcher asset_ids<2 ValueError — 심층 분석

**증상:**
- 프로덕션에서 `analyze_correlation_tool` 호출 시 `ValueError: At least 2 assets required for correlation`
- Reporter가 빈 데이터("도구 호출 실패")로 리포트 생성

**근본 원인:**
- Classifier가 `asset_ids: ["005930"]` (1개만) 반환
- `_build_tool_args`가 `asset_ids or None` 로직으로 1개 자산을 그대로 전달
- `compute_correlation`이 2개 미만 검증에서 ValueError 발생

**수정:**
- `_build_tool_args`에서 `analyze_correlation_tool`, `get_correlation` 모두 `asset_ids<2`이면 `None` 전달 → 전체 활성 자산 사용
- 에러 로깅 강화: tool args + exception type/message 상세 출력

**영향 파일:**
- `backend/api/services/llm/agentic/data_fetcher.py`
- `backend/api/services/chat/chat_service.py`
- `backend/api/services/llm/agentic/reporter.py`
- `backend/tests/unit/test_agentic_data_fetcher.py`

## 성능 최적화: Reporter 타임아웃 근본 원인 진단 및 모델 교체

### PERF-1: gpt-5-mini `temperature=0` 미지원 — 심층 분석

**증상:**
- Reporter가 간헐적으로 APITimeoutError 발생 → fallback_report("분석 결과를 생성하지 못했습니다") 반환
- 단순 API 테스트(curl)로는 2.26초 정상 → 외부 원인이 아님

**초기 오진:**
- "API 서버 느림" 또는 "JSON mode + 프롬프트 조합 문제"로 추정
- ❌ 실제로는 **모델 호환성 문제**

**근본 원인:**
- gpt-5-mini는 **reasoning 모델** (o1/o3 계열) — 발견 사실:
  1. `temperature=0` 미지원 → `BadRequestError 400` 즉시 발생
  2. langchain `ChatOpenAI`가 이 에러를 자동 재시도(max_retries=3) → 25초+ 소요
  3. `max_tokens` → `max_completion_tokens` 필요 (completion에 reasoning_tokens 포함)
  4. gpt-5-nano도 reasoning 모델 (reasoning_tokens=3,328, 36.9초)

**모델 벤치마크 (실제 tool_results, JSON mode):**

| 모델 | 시간 | reasoning tokens | 출력 품질 |
|------|------|-----------------|----------|
| gpt-5-mini | 34.8s | 2,240 | 1,135자 |
| gpt-5-nano | 36.9s | 3,328 | 921자 |
| gpt-4.1-mini | **4.5s** | 0 | 259자 |
| gpt-4o-mini | 4.9s | 0 | 195자 |

**수정:**
- Reporter 모델을 `gpt-4.1-mini`로 분리 (settings.py에 `llm_report_model` 추가)
- non-reasoning 모델이므로 `temperature=0` 복원, `request_timeout=30`
- Classifier는 gpt-5-mini(reasoning) 유지 — 질문 의도 파악에 적합
- Summarizer(gpt-5-nano) — `temperature=0` 제거 (reasoning 모델 호환)
- graph.py — timeout=60s, retries=2로 조정

**DataFetcher 캐시 효과 검증:**

| 시나리오 | 시간 | 비고 |
|----------|------|------|
| Cold (첫 요청) | 12.4s | DB 쿼리 |
| Warm (캐시 히트) | 1.3s | 9.2배 개선 |

**최종 E2E 실측:**
- Cold: Classifier 8s + Fetch 12s + Reporter 5.8s = **~26s**
- Warm: Classifier 8s + Fetch 1.3s + Reporter 5.8s = **~15s** (목표 달성)

**영향 파일:**
- `backend/config/settings.py` — `llm_report_model` 추가
- `backend/api/services/llm/agentic/reporter.py` — 모델 분리 + temperature=0
- `backend/api/services/llm/agentic/classifier.py` — temperature 제거, timeout/retries 조정
- `backend/api/services/llm/graph.py` — timeout/retries 조정
- `backend/api/services/chat/summarizer.py` — temperature=0 제거 (gpt-5-nano 호환)
- `backend/.env.example` — LLM_REPORT_MODEL 추가
- `backend/tests/unit/test_agentic_reporter.py` — 모델 분기 테스트 → 단일 모델 테스트로 변경

### PERF-2: Cache Warmup — DataFetcher Cold 최적화

**문제:**
- DataFetcher cold 요청 시 12s 소요 (DB 쿼리 + 계산)
- 인메모리 캐시(tool_cache.py)는 서버 재시작 시 소멸 → 첫 요청 항상 cold

**해결:**
- `cache_warmup.py` 신규 생성 — 서버 시작 시 주요 tool 결과를 백그라운드 프리페치
- 7개 자산 × 4개 tool + get_correlation = **29개 호출** 병렬 실행
- FastAPI lifespan hook (`asyncio.create_task`)로 비동기 실행 (서버 시작 블로킹 없음)
- 17초 소요, 29/29 성공

**결과:**

| 시나리오 | Before | After |
|---------|--------|-------|
| Cold (첫 요청) | 12s fetch | ~1.3s (캐시 히트) |
| E2E Cold | ~26s | ~15s (warm 수준) |

**영향 파일:**
- `backend/api/services/llm/agentic/cache_warmup.py` — 신규
- `backend/api/main.py` — lifespan에 warmup_cache() 추가

## Modified Files Summary

### Backend
```
backend/api/services/llm/agentic/
├── __init__.py          (F.1 신규)
├── schemas.py           (F.1 신규)
├── knowledge_prompts.py (F.2 신규)
├── classifier.py        (F.3 신규, F.10 JSON mode 전환)
├── data_fetcher.py      (F.4 신규, F.10 asset_ids 버그 수정)
├── reporter.py          (F.5 신규, F.10 JSON mode 전환)
├── tool_cache.py        (인메모리 당일 캐시)
├── compressor.py        (Tool Result 압축기)
└── cache_warmup.py      (서버 시작 시 프리페치 — Cold 최적화)

backend/api/services/chat/
└── chat_service.py      (F.6 핵심 리팩토링, F.10 에러 로깅)

backend/api/services/llm/
└── graph.py             (F.10 max_retries, 메시지 트리밍)

backend/tests/unit/
├── test_agentic_schemas.py      (F.1)
├── test_knowledge_prompts.py    (F.2)
├── test_agentic_classifier.py   (F.3, F.10)
├── test_agentic_data_fetcher.py (F.4, F.10)
├── test_agentic_reporter.py     (F.5, F.10)
├── test_hybrid_integration.py   (F.6)
└── test_api/test_chat_service.py (F.10)
```

### Frontend
```
frontend/src/
├── types/chat.ts                        (F.7 follow_up 타입)
├── hooks/useSSE.ts                      (F.7 follow_up 파싱)
├── store/chatStore.ts                   (F.7 followUpQuestions)
├── components/chat/ChatPanel.tsx        (F.7 follow-up UI, F.8 navigate)
├── components/charts/CorrelationHeatmap.tsx (F.10 highlight 시각)
└── pages/CorrelationPage.tsx            (F.10 highlightedPair 연결)
```

## Lessons Learned

### L1: OpenAI 529 에러를 "일시적"으로 단정하지 말 것
- 529 = 반드시 서버 문제가 아님. 요청 토큰 크기 과다, 누적 메시지, rate limit 등 클라이언트 측 원인일 수 있음
- API key 직접 테스트(GET /models)로 서버 정상 확인 → 요청 payload 문제로 의심 전환
- **교훈**: API 에러 발생 시 "서버 문제"로 단정하기 전에 요청 크기, 토큰 수, 재시도 로직 먼저 확인

### L2: LLM 호출에 반드시 timeout + retry 제한 설정
- `ChatOpenAI()` 기본값이 과도한 재시도를 유발할 수 있음
- 모든 LLM 호출에 `max_retries=3`, `request_timeout=10` 명시적 설정 필수
- MemorySaver 사용 시 메시지 트리밍 로직 필수

### L3: reasoning 모델 호환성 반드시 확인
- gpt-5-mini, gpt-5-nano는 **reasoning 모델** → `temperature`, `max_tokens` 파라미터 미지원
- langchain은 400 에러를 자동 재시도하므로 즉시 에러가 아닌 **느려짐**으로 나타남
- **교훈**: 새 모델 적용 시 reasoning/non-reasoning 여부 먼저 확인. reasoning 모델은 JSON 리포트 생성 같은 단순 작업에 과잉 — non-reasoning 모델이 4-7배 빠름

### L4: with_structured_output → JSON mode
- LangChain `with_structured_output(Pydantic)` 프로덕션에서 지속 실패
- `response_format=json_object` + 수동 `json.loads` + `Pydantic(**data)`로 전환하면 안정적
- **교훈**: LangChain 고수준 추상화가 프로덕션에서 실패할 수 있음. 저수준 직접 제어 선호

### L5: correlation tool에 자산 개수 방어
- `compute_correlation`은 2개 이상 자산 필요
- Classifier가 1개만 반환할 수 있으므로 `_build_tool_args`에서 방어 필요
- **교훈**: 외부 입력(LLM 출력)을 tool에 전달 전 반드시 validation
