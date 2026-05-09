# Phase F: Full Agentic Flow — Tasks
> Last Updated: 2026-03-19
> Status: Complete (10/10)
> Total: 10 tasks (S:5, M:4, L:1)

## Stage A: 기반 정의

- [x] F.1 Pydantic 스키마 정의 `[S]`
  - ClassificationResult (target_page, should_navigate, category, required_tools, asset_ids, params, confidence)
  - CuratedReport (summary, analysis, verdict, ui_actions, follow_up_questions)
  - UIActionModel (action: Literal, payload)
  - 신규: `backend/api/services/llm/agentic/__init__.py`, `schemas.py`
  - 테스트: `backend/tests/unit/test_agentic_schemas.py`

- [x] F.2 Knowledge Expert Prompts `[S]`
  - CLASSIFIER_PROMPT (9개 카테고리 + general 정의, required_tools 매핑)
  - PRICES_EXPERT_PROMPT, CORRELATION_EXPERT_PROMPT, INDICATORS_EXPERT_PROMPT, STRATEGY_EXPERT_PROMPT
  - get_knowledge_prompt(page_id) -> str
  - 신규: `backend/api/services/llm/agentic/knowledge_prompts.py`
  - 테스트: `backend/tests/unit/test_knowledge_prompts.py`

## Stage B: 핵심 모듈 구현

- [x] F.3 LLM Classifier `[M]` — depends: F.1, F.2
  - async classify_question(question, page_id, asset_ids, params) -> ClassificationResult
  - ChatOpenAI(model=llm_lite_model).with_structured_output(ClassificationResult)
  - 실패 시 ClassificationResult(category="general", confidence=0.0) 반환
  - 신규: `backend/api/services/llm/agentic/classifier.py`
  - 테스트: OpenAI mock → 파싱 검증, 에러 fallback 검증

- [x] F.4 DataFetcher `[M]` — depends: F.1
  - async fetch_data(classification: ClassificationResult) -> dict[str, Any]
  - tool name → tool function 매핑 dict (9개 tool)
  - classification.required_tools + params로 동적 호출
  - 개별 tool 실패 시 skip, 부분 결과 반환
  - name_map 자동 포함
  - 신규: `backend/api/services/llm/agentic/data_fetcher.py`
  - 테스트: tool .invoke() mock, 부분 실패 검증

- [x] F.5 LLM Reporter `[M]` — depends: F.1, F.2
  - async generate_report(category, tool_results, page_id, question, deep_mode) -> CuratedReport
  - deep_mode → gpt-5, else gpt-5-mini
  - system prompt = knowledge expert prompt + 공통 규칙
  - follow_up_questions 3개 동적 생성
  - ui_actions: LLM 판단 (UIActionModel로 타입 제한)
  - 신규: `backend/api/services/llm/agentic/reporter.py`
  - 테스트: OpenAI mock → CuratedReport 파싱, 모델 선택 검증

## Stage C: 백엔드 통합

- [x] F.6 chat_service.py 통합 `[L]` — depends: F.3, F.4, F.5
  - stream_chat 함수를 새 agentic flow로 교체
  - 유지: 세션 CRUD, _get_graph, LangGraph fallback, _status_event, _chunk_text
  - 제거: regex classify_question import, get_template_response import, _fetch_hybrid_data
  - is_nudge 파라미터: 시그니처 유지, 내부 무시
  - 수정: `backend/api/services/chat/chat_service.py`
  - 테스트: 기존 chat_service 테스트 업데이트 + agentic flow mock 테스트

## Stage D: 프론트엔드 확장

- [x] F.7 follow_up SSE + 프론트엔드 UI `[S]` — depends: F.6
  - 수정: `frontend/src/types/chat.ts` — follow_up SSE 타입
  - 수정: `frontend/src/hooks/useSSE.ts` — follow_up 이벤트 파싱 + 콜백
  - 수정: `frontend/src/store/chatStore.ts` — followUpQuestions 상태
  - 수정: `frontend/src/components/chat/ChatPanel.tsx` — follow-up 인라인 버튼

- [x] F.8 프론트엔드 navigate 핸들러 `[S]` — depends: F.6
  - useNavigate() import + handleUIAction case "navigate" 추가
  - 즉시 이동 (확인 없음)
  - 수정: `frontend/src/components/chat/ChatPanel.tsx`

## Stage E: 정리 + 검증

- [x] F.9 레거시 코드 정리 `[S]` — depends: F.6, F.7, F.8
  - hybrid/classifier.py — import 참조 제거, dead code 삭제
  - hybrid/templates.py — get_nudge_questions만 유지, 나머지 제거
  - 기존 hybrid 관련 테스트 업데이트/제거

- [x] F.10 통합 검증 `[M]` — depends: F.1~F.9 — `9511cf2`
  - Backend: 808 passed, ruff clean
  - Frontend: tsc 0 errors, vite build 성공
  - E2E 수동 테스트:
    - [x] correlation에서 "유사 자산 추천" → agentic flow + highlight_pair
    - [x] prices에서 "상관관계 보여줘" → 자동 navigate(/correlation) + 분석 결과
    - [x] "안녕하세요" → LangGraph fallback
    - [x] 넛지 클릭 → agentic flow (is_nudge 무관)
    - [x] follow-up 버튼 클릭 → 새 질문 전송
    - [x] deep mode 토글 → Reporter가 gpt-5 사용
  - Vercel + Railway 프로덕션 배포 완료
  - E2E 버그 수정: with_structured_output→JSON mode, DataFetcher asset_ids<2 ValueError

---

## Summary
- **Stage A**: 2 tasks (S:2) — 기반 정의
- **Stage B**: 3 tasks (M:3) — 핵심 모듈
- **Stage C**: 1 task (L:1) — 백엔드 통합
- **Stage D**: 2 tasks (S:2) — 프론트엔드
- **Stage E**: 2 tasks (S:1, M:1) — 정리+검증
- **Total**: 10 tasks (S:5, M:4, L:1)
- **파일 집계**: 신규 ~6 / 수정 ~6 / Migration 0
