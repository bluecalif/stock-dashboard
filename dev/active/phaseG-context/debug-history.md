# Phase G: User Context & Guided Experience — Debug History
> Last Updated: 2026-03-20

## Stage G-1: User Profile & Behavior Tracking

| Bug # | Page/Module | Issue | Fix | File |
|-------|-------------|-------|-----|------|
| G1-1 | profile_repo | `jsonb_set` nested path 생성 불가 (중간 키 없으면 실패) | 상위 키를 `'{}'::jsonb`로 보장하는 2-step 접근 | `profile_repo.py` |
| G1-2 | profile_repo | `activity_data`가 `json` 타입인데 `jsonb_set` 결과 타입 불일치 | `::json` 캐스트 추가 | `profile_repo.py` |
| G1-3 | profile_repo | `try/except`에서 에러 무시 → 200 OK 반환, 데이터 미저장 | 에러 로깅 강화 | `profile_repo.py` |

### G1-1/G1-2: jsonb_set nested path + json 타입 캐스트

**증상**: `increment_activity()`, `record_page_visit()`에서 `page_visits.prices` 같은 nested 경로 저장 실패. API는 200 OK 반환하지만 DB 데이터 없음.

**원인**:
1. PostgreSQL `jsonb_set`은 중간 키(`page_visits`)가 없으면 `{page_visits, prices}` 경로 생성 불가
2. `activity_data` 컬럼이 `json` 타입이므로 `jsonb_set` 결과를 `::json`으로 캐스트해야 함

**수정**: 상위 키 존재 보장 쿼리 추가 + `::json` 캐스트

## Stage G-2: Conversation Memory

| Bug # | Page/Module | Issue | Fix | File |
|-------|-------------|-------|-----|------|
| (버그 없음) | | | | |

## Stage G-3: Context-Aware Response & Guide

| Bug # | Page/Module | Issue | Fix | File |
|-------|-------------|-------|-----|------|
| (버그 없음) | | | | |

## E2E 브라우저 테스트 버그

| Bug # | Page/Module | Issue | Fix | File |
|-------|-------------|-------|-----|------|
| E2E-1 | chat.ts | SSE fetch가 axios 인터셉터 밖 → 401 시 토큰 갱신 안 됨 | `sendMessageSSE` 내 401 감지 + refresh + 재시도 로직 | `frontend/src/api/chat.ts` |
| E2E-2 | reporter.py | 복잡한 분석 질문에서 30초 타임아웃 부족 | request_timeout 30s → 45s, 에러 로그 강화 | `reporter.py` |
| E2E-3 | tools.py | LLM이 신호 성공률 null을 "산출 불가"로 오해 | `note` 필드 추가 + knowledge_prompts 가이드 | `tools.py`, `knowledge_prompts.py` |
| E2E-4 | tools.py | 그래프 API vs LLM API 신호 성공률 데이터 소스 불일치 | ⚠️ 미수정 — `analyze_indicators` 툴이 strategy-based 사용, 그래프는 indicator-based | `tools.py` |

### E2E-4: 신호 성공률 데이터 소스 불일치 (미수정)

**증상**: 대시보드 그래프에는 RSI/MACD 성공률 표시되지만, 챗봇은 "산출 불가" 응답.

**원인**: `analyze_indicators` 툴(Phase D.5)이 `compute_signal_accuracy(strategy_id)` 사용. 그래프는 `compute_indicator_accuracy(indicator_id)` 사용 (Phase DR.2에서 추가). D.5 시점에 indicator-based 함수 미존재 → LLM 툴 미업데이트.

**수정 계획**: `analyze_indicators`에 `compute_indicator_accuracy("rsi_14"/"macd")` 호출 추가 → `indicator_accuracy` 키로 반환. plan 파일 참조.

## Modified Files Summary

```
backend/
├── api/
│   ├── repositories/profile_repo.py        — jsonb nested path + json 캐스트 수정
│   ├── services/
│   │   ├── chat/
│   │   │   ├── chat_service.py             — activity tracking, 요약 트리거, user_context 파이프
│   │   │   ├── summarizer.py               — gpt-4o-mini 요약 수정
│   │   │   └── user_context.py             — 신규: UserContext 빌더
│   │   └── llm/
│   │       ├── agentic/
│   │       │   ├── classifier.py           — user_context 파라미터 추가
│   │       │   ├── reporter.py             — user_context + timeout 45s
│   │       │   ├── schemas.py              — unsupported 카테고리
│   │       │   └── knowledge_prompts.py    — 동적 프롬프트 + 성공률 가이드
│   │       └── tools.py                    — signal accuracy note 필드
│   └── tests/unit/
│       ├── test_agentic_classifier.py      — user_context 테스트 추가
│       ├── test_agentic_reporter.py        — user_context 테스트 추가
│       └── test_api/
│           ├── test_chat_service.py        — activity + 요약 테스트 추가
│           ├── test_summarizer.py          — 수정
│           └── test_user_context.py        — 신규: UserContext 테스트
frontend/
├── src/
│   ├── api/chat.ts                         — SSE 401 token refresh
│   ├── components/
│   │   ├── layout/Layout.tsx               — PageGuide 통합
│   │   └── onboarding/PageGuide.tsx        — 신규: 첫 방문 안내
│   └── tailwind.config.js                  — PageGuide 애니메이션
```

## Lessons Learned

1. **PostgreSQL jsonb_set nested path**: 중간 키가 없으면 nested path 생성 불가. 상위 키 보장 → 하위 키 설정 2-step 필요.
2. **json vs jsonb 타입**: `json` 컬럼에 `jsonb_set` 결과 저장 시 `::json` 캐스트 필수.
3. **SSE와 axios 인터셉터**: `fetch` API는 axios 인터셉터 범위 밖. SSE 스트리밍에서 별도 401 처리 필요.
4. **LLM 툴 데이터 소스 일관성**: 그래프 API와 LLM 툴이 동일 데이터 소스를 사용해야 함. 새 분석 함수 추가 시 LLM 툴도 업데이트 필요.
5. **try/except 무시 패턴 위험**: DB 쓰기 에러를 조용히 삼키면 API 200 OK + 데이터 미저장 → 디버깅 매우 어려움.
