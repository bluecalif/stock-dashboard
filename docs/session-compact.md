# Session Compact

> Generated: 2026-03-21 (세션 3)
> Source: Conversation compaction via /compact-and-go

## Goal
G-2/G-3 검증 + 채팅 품질 개선 (대화 히스토리, unsupported 라우팅, 서버 관리 디버깅)

## Completed
- [x] **G-2 대화 요약 검증** (`70d125b`)
  - `_run_summary()` 요청 스코프 DB 세션 버그 수정 → 자체 `SessionLocal()` 생성
  - E2E: 5턴 후 `conversation_summaries` 1건 생성, `user_profiles.top_assets`/`top_categories` 갱신 확인
- [x] **G-3 Context-Aware 검증** (`70d125b`)
  - beginner vs expert 프로필 변경 시 응답 톤/깊이 차이 브라우저 E2E 확인
- [x] **채팅 대화 히스토리 전달** (`ca162dd`)
  - Classifier + Reporter에 최근 3턴(6개 메시지) `chat_history` 전달
  - Classifier: 이전 대화 100자 요약으로 토큰 절약
  - Reporter: 이전 대화 200자 요약으로 토큰 절약
  - "아까 그 종목" 등 이전 대화 참조 가능
- [x] **unsupported 질문 라우팅 개선** (`ca162dd`)
  - 하드코딩 거부 메시지 제거 → LangGraph fallback으로 일반 대화 처리
  - LangGraph 시스템 프롬프트: 일반 질문은 도구 없이 직접 답변 허용
  - "한국의 수도는" 같은 일반 질문 정상 답변 확인
- [x] **디버그 이력 상세화** (`ca162dd`)
  - debug-history.md: G2-1, E2E-5~8 상세 기록
  - Lessons Learned: DB 세션 누출, Windows uvicorn 좀비 프로세스, Agentic 단일턴 한계

## Current State

### Git 상태
- 최신 커밋: `ca162dd` (master, pushed)
- 미커밋 변경: 없음 (clean, `_context.md`와 `bash.exe.stackdump`만 untracked)

### 변경된 파일 (이번 세션 전체, 커밋 2건)
- `backend/api/services/chat/chat_service.py` — _run_summary DB 세션 수정 + 대화 히스토리 전달 + unsupported 거부 제거
- `backend/api/services/llm/agentic/classifier.py` — chat_history 파라미터 + 이전 대화 섹션
- `backend/api/services/llm/agentic/reporter.py` — chat_history 파라미터 + 이전 대화 섹션
- `backend/api/services/llm/prompts.py` — 일반 대화 도구 없이 답변 허용
- `backend/tests/unit/test_api/test_chat_service.py` — unsupported 테스트 업데이트
- `dev/active/phaseG-context/debug-history.md` — G2-1, E2E-5~8 + Lessons Learned
- `docs/session-compact.md` — TODO 업데이트

## Remaining / TODO

### 채팅 품질
- [x] 대시보드-채팅 일치성: 지표/시그널 페이지에서 시그널+성공률 탭 통합 설명 정책 결정
- [x] 대시보드-채팅 일치성: 종목/기간/시점을 응답에 항상 명시하도록 개선
- [x] 타임프레임 정렬: 대시보드/백테스트/지표/채팅 간 기본 기간 일치 (성공률 기본 1년) — TF-1~7 수정

### 기타
- [x] 회원 탈퇴 기능 추가 — `aad7e9e`
- [x] 대시보드(홈) 데이터가 현재 기준으로 업데이트 안 되는 문제 수정 — TF-1 (get_latest_prices)

### 후순위
- [ ] Reporter LLM 응답 시간 ~22초 성능 최적화 검토
- [ ] 프로덕션 배포 테스트

### 프로젝트 마무리
- [x] README.md 작성 — `04260e9`
- [x] project-wrapup 커맨드 생성 (교훈, 재사용 패턴, 설계 순서도, 총괄 요약)
- [ ] `/project-wrapup` 실행

## Key Decisions
- **unsupported → LangGraph fallback**: 일반 대화도 처리 가능하도록 거부 메시지 대신 LangGraph로 라우팅
- **대화 히스토리 3턴 제한**: 토큰 비용 vs 맥락 유지 균형. Classifier 100자, Reporter 200자로 요약
- **백그라운드 태스크 자체 DB 세션**: asyncio.ensure_future로 넘기는 태스크는 요청 스코프 세션 사용 금지

## Context
- 다음 세션에서는 답변에 한국어를 사용하세요.
- **프로젝트 상태**: 전 Phase 완료 (MVP~Phase G, 858 tests)
- **E2E 플로우**: Classifier(2s) → DataFetcher(8s) → Reporter(22s) → 응답
- **핵심 참조**: `dev/active/phaseG-context/debug-history.md` (상세 디버그 이력)
- **서버 관리 주의**: Windows uvicorn --reload 간헐적 실패. 코드 변경 미반영 시 `tasklist`로 좀비 프로세스 확인 → 전부 `taskkill` → 재시작

## Project Status

| Phase | 상태 | 비고 |
|-------|------|------|
| MVP (0~7) | ✅ 완료 | 83/83 tasks |
| Phase A Auth | ✅ 완료 | 16/16 tasks |
| Phase B Chatbot | ✅ 완료 | 19/19 tasks |
| Phase C 상관도 | ✅ 완료 | 12/12 Steps |
| Phase C-rev 피드백 | ✅ 완료 | 7/7 Tasks |
| Phase C-rev2 피드백 | ✅ 완료 | 4/4 Tasks |
| Phase D 지표 | ✅ 완료 | 12/12 Tasks |
| Phase D-rev 피드백 | ✅ 완료 | 13/13 Tasks |
| Phase D-improve | ✅ 완료 | 7/7 Tasks |
| Phase E 전략 | ✅ 완료 | 10/10 Tasks |
| Phase F Agentic | ✅ 완료 | 10/10 Tasks |
| Phase G Context | ✅ 완료 | 20/20 tasks |

## Next Action
다음 세션에서 유저의 구체적 지시를 기다린 후 진행. 우선 후보:
1. 대시보드-채팅 일치성 (지표/시그널 설명 정책 + 종목/기간 명시)
2. 회원 탈퇴 기능
3. 대시보드 데이터 갱신 문제
