# Session Compact

> Generated: 2026-03-18 21:30
> Source: Phase F Agentic Flow 구현 + E2E 테스트 피드백

## Goal
Phase F: Full Agentic Flow 구현 — regex classifier + f-string 템플릿 → 2-Step LLM Structured Output (Classifier + Reporter) 전환 + 자동 페이지 네비게이션 + follow-up 질문 UI.

## Completed
- [x] F.1 Pydantic 스키마 정의 (ClassificationResult, CuratedReport, UIActionModel) — `schemas.py`
- [x] F.2 Knowledge Expert Prompts (Classifier + 4개 페이지 전문가) — `knowledge_prompts.py`
- [x] F.3 LLM Classifier (Structured Output, gpt-5-mini) — `classifier.py`
- [x] F.4 DataFetcher (9개 tool 프로그래밍적 호출) — `data_fetcher.py`
- [x] F.5 LLM Reporter (Structured Output, knowledge prompt) — `reporter.py`
- [x] F.6 chat_service.py 통합 (agentic flow 전환)
- [x] F.7 follow_up SSE 이벤트 + 프론트엔드 UI (ChatPanel에 follow-up 버튼)
- [x] F.8 프론트엔드 navigate 핸들러 (useNavigate + handleUIAction)
- [x] F.9 레거시 코드 정리
- [x] F.10 통합 검증 — 805 passed, ruff clean, tsc 0 errors, vite build 성공
- [x] 커밋 `10099ca` + push → Railway/Vercel 프로덕션 배포 완료

## E2E 테스트 결과 (프로덕션 브라우저)
- **#1 correlation "유사 자산 추천"**: ✅ agentic flow 동작, ❌ highlight_pair 시각적 효과 안 보임
- **#2 prices "상관관계 보여줘"**: ❌ 자동 navigate 안 됨 — LLM이 should_navigate 미설정 가능성 + 결정적 보정 코드 추가했으나 미커밋
- **#3 "안녕하세요"**: ✅ LangGraph fallback 정상
- **#4 넛지 클릭**: ❌ agentic flow 대신 LangGraph fallback만 표시 ("AI가 생각하고 있어요...")
- **#5 follow-up 버튼**: ❌ 보이지 않음 — LLM이 빈 배열 반환 또는 `_default_follow_ups` 함수 미정의 (코드에 참조만 있고 함수 없음)
- **#6 deep mode 토글**: ✅ 정상
- **overloaded_error 529**: ❌ "일시적 과부하"가 아님 — MemorySaver 토큰 누적 + 재시도 과다가 근본 원인 (아래 Bug 4 참조)

## Critical Bugs (미커밋, 미수정)

### Bug 1: `_default_follow_ups` 함수 미정의
- `chat_service.py:210`에서 `_default_follow_ups(classification.target_page)` 호출하지만 함수가 정의되어 있지 않음
- **런타임 NameError 발생** → agentic flow 전체가 깨질 수 있음
- 수정: `_default_follow_ups` 함수 추가 또는 fallback 로직 변경 필요

### Bug 2: Agentic flow가 실제로 작동하지 않는 것으로 의심됨
- 사용자가 "AI가 생각하고 있어요..."만 보임 → LangGraph fallback만 실행 중
- 원인 추정:
  1. LLM Classifier가 OpenAI API 호출 실패 → `confidence=0.0` fallback → 항상 LangGraph
  2. OpenAI API overloaded (529 에러 목격)
  3. 또는 `_default_follow_ups` NameError로 이전 agentic 시도가 에러 → 전체 에러 핸들링 미흡
- **Railway 로그 확인 필요** — classifier가 실제로 호출되는지, 에러 로그가 있는지

### Bug 4: 529 Overloaded Error — 토큰 누적 + 재시도 과다
- 초기 오진: "일시적 서버 과부하" → ❌ 틀림. API key 직접 테스트 시 200 OK
- **실제 원인**: MemorySaver가 세션 전체 대화 이력 누적 → 토큰 폭발 → 529
- **악화 요인**: ChatOpenAI 기본 재시도(10회 × 25초) → 사용자 250초 대기
- **수정**: (1) max_retries=3, request_timeout=10 설정 (2) 메시지 이력 트리밍 (3) 이전 대화 클리어
- **영향**: classifier.py, reporter.py, graph.py

### Bug 3: highlight_pair 시각적 효과 미반영
- chartActionStore에 `setHighlightedPair` 호출은 되지만, 실제 히트맵 컴포넌트에서 해당 상태를 소비하여 시각적 강조를 하는 로직이 없을 수 있음

## Current State

### Git 상태
- 최신 커밋: `10099ca` (master, push 완료, Railway/Vercel 배포됨)
- **미커밋 변경**: `chat_service.py`에 navigate 결정적 보정 + follow_up fallback 코드 추가됨 (but `_default_follow_ups` 함수 미정의!)

### 테스트 상태
- Backend: 805 passed, ruff clean (커밋 시점)
- Frontend: tsc 0 errors, vite build 성공 (커밋 시점)
- **주의**: 미커밋 변경에 `_default_follow_ups` 미정의 → 현재 로컬 코드는 깨진 상태

### 인프라 상태
- **Railway**: `https://backend-production-e5bc.up.railway.app` — Active, Online
- **Vercel**: `https://stock-dashboard-alpha-lilac.vercel.app` — 200 OK
- **프로덕션은 `10099ca` 커밋 기준** — 미커밋 변경은 반영 안 됨

### 신규 파일 (이번 세션)
- `backend/api/services/llm/agentic/__init__.py` — 패키지
- `backend/api/services/llm/agentic/schemas.py` — Pydantic 스키마
- `backend/api/services/llm/agentic/knowledge_prompts.py` — 5개 프롬프트
- `backend/api/services/llm/agentic/classifier.py` — LLM 질문 분류기
- `backend/api/services/llm/agentic/data_fetcher.py` — 9개 tool 동적 호출
- `backend/api/services/llm/agentic/reporter.py` — LLM 리포트 생성
- `backend/tests/unit/test_agentic_*.py` — 테스트 5개 파일 (67개 테스트)
- `dev/active/phaseF-agentic/` — dev docs

### 수정 파일
- `backend/api/services/chat/chat_service.py` — agentic flow 전환 (핵심)
- `backend/tests/unit/test_hybrid_integration.py` — 테스트 업데이트
- `frontend/src/types/chat.ts` — follow_up SSE 타입
- `frontend/src/hooks/useSSE.ts` — follow_up 이벤트 파싱
- `frontend/src/store/chatStore.ts` — followUpQuestions 상태
- `frontend/src/components/chat/ChatPanel.tsx` — navigate + follow-up UI

## Key Decisions
- **2-Step LLM**: Classifier(gpt-5-mini) → DataFetcher(프로그래밍적) → Reporter(gpt-5/mini)
- **Confidence threshold 0.5**: 미만이면 LangGraph fallback
- **category="general"이면 항상 LangGraph**: 높은 confidence여도 fallback
- **is_nudge 파라미터 무시**: 시그니처는 유지하되 내부에서 구분 없음 (모든 질문이 agentic flow)
- **navigate 결정적 보정**: target_page != current_page이면 LLM 판단과 무관하게 navigate (미커밋)

## Context
- 다음 세션에서는 답변에 한국어를 사용하세요.
- **피드백 원본**: `docs/post-mvp-feedback.md`
- **기존 코드 패턴**: Router-Service-Repository 3계층, 함수형 repo, Pydantic v2, SQLAlchemy 2.0 Mapped
- **Frontend**: React 19 + Vite + TypeScript + Tailwind + zustand + Recharts + react-router-dom v6
- **SSE 주의**: EventSource(GET) 사용 금지 → fetch + ReadableStream 사용
- **OpenAI 529 overloaded_error**: 서버 일시 과부하가 아님. MemorySaver 토큰 누적 + 재시도 과다가 근본 원인. max_retries=3 + 메시지 트리밍 필요.
- **Phase F 계획 문서**: `dev/active/phaseF-agentic/phaseF-agentic-plan.md`

## Project Status

| Phase | 상태 | 비고 |
|-------|------|------|
| MVP (0~7) | ✅ 완료 | 83/83 tasks |
| Phase A Auth | ✅ 완료 | 16/16 tasks |
| Phase B Chatbot | ✅ 완료 | 19/19 tasks |
| Phase C 상관도 | ✅ 완료 | 12/12 Steps |
| Phase C-rev 피드백 | ✅ 완료 | 7/7 Tasks |
| Phase C-rev2 피드백 | ✅ 완료 | 4/4 Tasks + 품질 개선 |
| Phase D 지표 | ✅ 완료 | 12/12 Tasks |
| Phase D-rev 피드백 | ✅ 완료 | 13/13 Tasks |
| Phase D-improve | ✅ 완료 | 7/7 Tasks + E2E 수정 |
| Phase E 전략 | ✅ 완료 | 10/10 Tasks |
| Phase F Agentic | 🔧 E2E 수정 중 | 코드 완료, 프로덕션 E2E 버그 4건 |
| Phase G~H | ⬜ 미시작 | Memory/Onboarding |

## Next Action
Phase F E2E 버그 수정 (우선순위 재정렬):

1. **🔴 529 에러 해결** — 모든 ChatOpenAI에 `max_retries=3`, `request_timeout=10` 설정 + LangGraph 메시지 트리밍 + 이전 대화 클리어
2. **`_default_follow_ups` 함수 정의** — chat_service.py에 추가 (NameError 해결)
3. **Agentic flow 작동 확인** — 529 해결 후 classifier가 정상 호출되는지 검증
4. **follow-up 버튼 표시 수정** — SSE 이벤트 전송 확인
5. **navigate 동작 확인** — 결정적 보정 코드 커밋 + 테스트
6. **highlight_pair 시각적 효과** — 히트맵 컴포넌트에서 highlightedPair 상태 소비 확인
7. 수정 후 재배포 + E2E 재테스트
