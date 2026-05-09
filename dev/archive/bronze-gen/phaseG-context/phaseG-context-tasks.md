# Phase G: User Context & Guided Experience — Tasks
> Last Updated: 2026-03-20
> Status: ✅ 완료 (20/20)

## Stage G-1: User Profile & Behavior Tracking (9/9) ✅

### Backend 기반
- [x] G.1 DB 모델: UserProfile, UserActivity + models.py 추가 `[M]`
- [x] G.2 Alembic 마이그레이션: user_profiles, user_activity 테이블 `[S]`
- [x] G.3 Repository: profile_repo.py (CRUD + JSONB increment) `[M]`
- [x] G.4 Pydantic 스키마: profile.py (IceBreaking + Profile + Activity) `[S]`
- [x] G.5 API 엔드포인트: profile router (4 endpoints) + main.py 등록 `[M]`

### Backend 통합
- [x] G.6 chat_service Activity 통합 (질문 카운터, 자산 조회수, deep_mode) `[M]`

### Frontend
- [x] G.7 Frontend: Ice-breaking 모달 + profileStore + API client `[L]`
- [x] G.8 Frontend: usePageTracking hook + Layout.tsx 통합 `[S]`

### 테스트
- [x] G.9 G-1 테스트: profile_repo + profile_router + activity_tracking `[M]` — 18 tests

## Stage G-2: Conversation Memory (5/5) ✅

### Backend 기반
- [x] G.10 DB 모델 + 마이그레이션: ConversationSummary 테이블 `[S]`
- [x] G.11 Repository 확장: chat_repo.py — upsert_summary, get_recent_summaries `[S]`

### 핵심 서비스
- [x] G.12 LLM 세션 요약 서비스: summarizer.py (gpt-4o-mini, JSON mode) `[L]`
- [x] G.13 stream_chat 통합: 5턴 요약 트리거 + user_profile 갱신 `[M]`

### 테스트
- [x] G.14 G-2 테스트: summarizer + summary_repo `[M]` — 8 tests

## Stage G-3: Context-Aware Response & Guide (6/6) ✅

### Backend 프롬프트 수정
- [x] G.15 UserContext 구조 + Classifier 프롬프트 수정 (user_context 파라미터) `[M]`
- [x] G.16 Reporter 프롬프트 수정 (톤/깊이 조정 + 이전 맥락 주입) `[M]`
- [x] G.17 stream_chat UserContext 파이프라인 연결 `[M]`

### 기능 확장
- [x] G.18 Dynamic Nudge + "unsupported" 카테고리 `[M]`

### Frontend
- [x] G.19 Frontend: PageGuide 컴포넌트 (beginner 첫 방문 안내) `[S]`

### 통합 검증
- [x] G.20 G-3 테스트 + 전체 통합 검증 (858 tests, ruff clean) `[M]`

---

## Summary

| Sub-phase | Tasks | Size 분포 | 상태 |
|-----------|-------|-----------|------|
| G-1 | 9 | S:2, M:5, L:1 | ✅ 완료 (9/9) |
| G-2 | 5 | S:2, M:2, L:1 | ✅ 완료 (5/5) |
| G-3 | 6 | S:1, M:5 | ✅ 완료 (6/6) |
| **Total** | **20** | **S:5, M:12, L:2** | **20/20 ✅** |

**파일 집계**: 신규 13 / 수정 12 / Migration 2
