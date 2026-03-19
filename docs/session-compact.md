# Session Compact

> Generated: 2026-03-19 19:00
> Source: Phase G Stage G-1 + G-2 구현 완료

## Goal
Phase G "User Context & Guided Experience" 구현: G-1 (User Profile & Behavior Tracking) + G-2 (Conversation Memory) + G-3 (Context-Aware Response).

## Completed
- [x] 디버그 console.log 제거 (useSSE.ts, ChatPanel.tsx)
- [x] **Stage G-1 완료 (9/9)**: DB 모델 + 마이그레이션 + Repository + 스키마 + API + chat_service Activity + Ice-breaking 모달 + usePageTracking + 테스트 18개
- [x] **Stage G-2 완료 (5/5)**: ConversationSummary 모델 + 마이그레이션 + chat_repo 확장 + summarizer.py + stream_chat 5턴 요약 트리거 + 테스트 8개

## Current State

### Git 상태
- 최신 커밋: `edd06f8` (master) + 미커밋 변경 (G-1, G-2 구현)
- 834 tests, ruff clean

### 생성된 파일 (신규)
- `backend/api/repositories/profile_repo.py` — Profile/Activity CRUD
- `backend/api/schemas/profile.py` — Pydantic 스키마
- `backend/api/routers/profile.py` — Profile API (4 endpoints)
- `backend/api/services/chat/summarizer.py` — LLM 세션 요약
- `backend/db/alembic/versions/b3f1a2c4e567_*.py` — user_profiles + user_activity 마이그레이션
- `backend/db/alembic/versions/c4d2e5f6a789_*.py` — conversation_summaries 마이그레이션
- `frontend/src/types/profile.ts` — TypeScript 타입
- `frontend/src/api/profile.ts` — API 클라이언트
- `frontend/src/store/profileStore.ts` — Zustand 스토어
- `frontend/src/components/onboarding/IceBreakingModal.tsx` — 2문항 모달
- `frontend/src/hooks/usePageTracking.ts` — 페이지 방문 추적
- `backend/tests/unit/test_api/test_profile_router.py` — 10 tests
- `backend/tests/unit/test_api/test_repositories/test_profile_repo.py` — 8 tests
- `backend/tests/unit/test_api/test_repositories/test_chat_repo_summary.py` — 5 tests
- `backend/tests/unit/test_api/test_summarizer.py` — 3 tests

### 수정된 파일
- `backend/db/models.py` — UserProfile, UserActivity, ConversationSummary 모델 추가
- `backend/api/main.py` — profile router 등록
- `backend/api/repositories/chat_repo.py` — summary CRUD 추가
- `backend/api/services/chat/chat_service.py` — activity tracking + 5턴 요약 트리거
- `frontend/src/App.tsx` — IceBreaking 모달 + profileStore 통합
- `frontend/src/components/layout/Layout.tsx` — usePageTracking 통합
- `frontend/src/hooks/useSSE.ts` — console.log 제거
- `frontend/src/components/chat/ChatPanel.tsx` — console.log 제거

## Remaining / TODO
- [ ] **Phase G-3 구현 시작** (6 tasks)
  - G.15 UserContext 구조 + Classifier 프롬프트 수정
  - G.16 Reporter 프롬프트 수정
  - G.17 stream_chat UserContext 파이프라인 연결
  - G.18 Dynamic Nudge + "unsupported" 카테고리
  - G.19 Frontend: PageGuide 컴포넌트
  - G.20 G-3 테스트 + 통합 검증

## Key Decisions
- **Phase G+H 통합**: H(Onboarding)는 G(Memory)의 선행 조건이므로 단일 Phase로 통합
- **pgvector 미사용**: 7자산×5페이지 한정 도메인에서 구조화 쿼리가 더 정확/빠름
- **JSONB 집계**: user_activity는 1 row per user, 카운터 increment 방식
- **Ice-breaking 2문항**: 경험 수준 + 의사결정 성향
- **Lazy creation**: 기존 users 대상 data migration 불필요. 첫 접근 시 UPSERT
- **gpt-4o-mini 요약**: 5턴마다 자동 세션 요약, done SSE 후 백그라운드 실행
- **하위 호환**: 모든 새 파라미터 default=None → 기존 808 테스트 영향 없음
- **Activity tracking 비차단**: try/except + rollback, 실패해도 채팅 흐름 유지

## Context
- 다음 세션에서는 답변에 한국어를 사용하세요.
- **Phase G dev-docs**: `dev/active/phaseG-context/` (4개 파일)

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
| Phase G Context | 🔨 구현 중 | 14/20 tasks (G-1 ✅, G-2 ✅, G-3 미시작) |

## Next Action
**Phase G-3 구현**: G.15 (UserContext 구조 + Classifier 프롬프트 수정)부터 시작.
