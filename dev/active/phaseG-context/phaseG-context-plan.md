# Phase G: User Context & Guided Experience
> Last Updated: 2026-03-19
> Status: In Progress — G-1 ✅, G-2 ✅, G-3 미시작

## 1. Summary (개요)

**목적**: Phase G(Memory+Retrieval) + Phase H(Onboarding)를 통합하여 사용자 프로필링 → 대화 메모리 → 맥락 기반 응답을 단일 Phase로 구현.

**범위**:
- G-1: User Profile & Behavior Tracking (DB + API + Ice-breaking + Activity)
- G-2: Conversation Memory (세션 요약 + LLM 기반 자동 생성)
- G-3: Context-Aware Response & Guide (프롬프트 주입 + Dynamic Nudge + Page Guide + Unsupported)

**예상 결과물**:
- `user_profiles`, `user_activity`, `conversation_summaries` DB 테이블
- Profile CRUD + Ice-breaking API
- LLM 기반 5턴마다 자동 세션 요약
- Classifier/Reporter에 사용자 맥락 주입 → 개인화 응답
- 동적 nudge 질문 (경험 수준 + 관심 자산 반영)
- 첫 방문 페이지 가이드 (beginner 전용)
- "unsupported" 카테고리 (범위 밖 질문 안내)

## 2. Current State (현재 상태)

- Phase F(Agentic Flow) 완료: 2-Step LLM (Classifier + Reporter) + 자동 네비게이션
- 834 tests passed, ruff clean
- **G-1 완료**: UserProfile/UserActivity DB + profile_repo + profile router 4 endpoints + Ice-breaking 모달 + usePageTracking + chat_service activity tracking
- **G-2 완료**: ConversationSummary DB + chat_repo summary CRUD + summarizer.py (gpt-4o-mini) + 5턴 요약 트리거
- G-3 미시작: Classifier/Reporter 프롬프트 수정, Dynamic Nudge, PageGuide

## 3. Target State (목표 상태)

| 영역 | 목표 | 현재 |
|------|------|------|
| 사용자 프로필 | Ice-breaking + 행동 기반 프로파일링 | ❌ 없음 |
| 활동 추적 | 페이지/자산/질문 카테고리별 카운터 | ❌ 없음 |
| 대화 메모리 | 5턴마다 자동 요약, 세션 간 맥락 유지 | ❌ 세션 내만 |
| 응답 개인화 | Classifier/Reporter가 사용자 맥락 참조 | ❌ 동일 응답 |
| Nudge 질문 | 경험 수준 + 관심 자산 기반 동적 생성 | 하드코딩 |
| 페이지 가이드 | 첫 방문 시 beginner 대상 안내 | ❌ 없음 |
| 범위 밖 처리 | "unsupported" 카테고리 + 안내 | ❌ 없음 |

## 4. Implementation Stages

### Stage G-1: User Profile & Behavior Tracking

**목적**: DB 스키마 + Profile CRUD + Ice-breaking + Activity Tracking

| Step | 설명 | Size | 의존성 |
|------|------|------|--------|
| 1.1 | DB 모델 (UserProfile, UserActivity) | M | - |
| 1.2 | Alembic 마이그레이션 | S | 1.1 |
| 1.3 | Repository (profile_repo.py) | M | 1.1 |
| 1.4 | Pydantic 스키마 (profile.py) | S | 1.3 |
| 1.5 | API 엔드포인트 (profile router) | M | 1.3, 1.4 |
| 1.6 | chat_service Activity 통합 | M | 1.3 |
| 1.7 | Frontend — Ice-breaking 모달 + Store | L | 1.5 |
| 1.8 | Frontend — Page Visit Tracking Hook | S | 1.5 |
| 1.9 | 테스트 (repo + router + activity) | M | 1.1~1.8 |

### Stage G-2: Conversation Memory

**목적**: LLM 기반 자동 세션 요약 + user_profile 행동 갱신

| Step | 설명 | Size | 의존성 |
|------|------|------|--------|
| 2.1 | DB 모델 (ConversationSummary) | S | - |
| 2.2 | Alembic 마이그레이션 | S | 2.1 |
| 2.3 | Repository 확장 (chat_repo.py) | S | 2.1 |
| 2.4 | LLM 세션 요약 서비스 (summarizer.py) | L | 2.3 |
| 2.5 | stream_chat 통합 — 요약 트리거 | M | 2.4 |
| 2.6 | user_profile 행동 데이터 갱신 | S | G-1, 2.4 |
| 2.7 | 테스트 (summarizer + repo) | M | 2.1~2.6 |

### Stage G-3: Context-Aware Response & Guide

**목적**: Classifier/Reporter 프롬프트에 사용자 맥락 주입 + 동적 Nudge + Page Guide

| Step | 설명 | Size | 의존성 |
|------|------|------|--------|
| 3.1 | UserContext 데이터 구조 (user_context.py) | S | G-1, G-2 |
| 3.2 | Classifier 프롬프트 수정 | M | 3.1 |
| 3.3 | Reporter 프롬프트 수정 | M | 3.1 |
| 3.4 | stream_chat에 UserContext 연결 | M | 3.1~3.3 |
| 3.5 | Dynamic Nudge Questions | M | 3.1 |
| 3.6 | "unsupported" 카테고리 | M | - |
| 3.7 | Frontend — Page Guide (beginner) | S | G-1 |
| 3.8 | 테스트 (context + nudge + unsupported) | M | 3.1~3.7 |

## 5. Task Breakdown

| Task ID | 설명 | Size | Sub-phase |
|---------|------|------|-----------|
| G.1 | DB 모델 (UserProfile, UserActivity) | M | G-1 |
| G.2 | Alembic 마이그레이션 (profile + activity) | S | G-1 |
| G.3 | Repository (profile_repo.py) | M | G-1 |
| G.4 | Pydantic 스키마 (profile.py) | S | G-1 |
| G.5 | API 엔드포인트 (profile router) | M | G-1 |
| G.6 | chat_service Activity 통합 | M | G-1 |
| G.7 | Frontend — Ice-breaking 모달 + Store | L | G-1 |
| G.8 | Frontend — Page Visit Tracking | S | G-1 |
| G.9 | G-1 테스트 | M | G-1 |
| G.10 | DB 모델 (ConversationSummary) + 마이그레이션 | S | G-2 |
| G.11 | Repository 확장 (summary CRUD) | S | G-2 |
| G.12 | LLM 세션 요약 서비스 | L | G-2 |
| G.13 | stream_chat 요약 트리거 + profile 갱신 | M | G-2 |
| G.14 | G-2 테스트 | M | G-2 |
| G.15 | UserContext 구조 + Classifier 수정 | M | G-3 |
| G.16 | Reporter 프롬프트 수정 | M | G-3 |
| G.17 | stream_chat UserContext 파이프라인 | M | G-3 |
| G.18 | Dynamic Nudge + unsupported 카테고리 | M | G-3 |
| G.19 | Frontend — Page Guide | S | G-3 |
| G.20 | G-3 테스트 + 통합 검증 | M | G-3 |

**Total: 20 tasks (S:6, M:11, L:2, XL:0)**

## 6. Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Railway 마이그레이션 실패 | 배포 차단 | 저 | 새 테이블 추가만 (기존 데이터 무영향), 로컬 테스트 선행 |
| LLM 요약 비용 증가 | 운영비 | 저 | gpt-4o-mini 사용, 5턴마다 1회만, 월 $2-5 예상 |
| 기존 808 테스트 깨짐 | 회귀 | 저 | 모든 새 파라미터 default=None (하위 호환) |
| JSONB 동시 업데이트 경합 | 데이터 누락 | 저 | 단일 사용자 접근 패턴, PostgreSQL JSONB 원자적 연산 |
| 프롬프트 길이 증가 | 토큰 비용 | 저 | user context ~200-300 토큰 (기존 대비 10-15%) |
| Ice-breaking 스킵 | 프로필 미완성 | 중 | 행동 기반 점진적 프로파일링으로 보완 |

## 7. Dependencies

### 내부
- Phase A (Auth): `users` 테이블 FK 참조
- Phase B (Chat): `chat_sessions`, `chat_messages` 테이블 참조
- Phase F (Agentic): Classifier/Reporter/knowledge_prompts 수정

### 외부
- OpenAI API: gpt-4o-mini (세션 요약용)
- Railway PostgreSQL: JSONB 지원 (기본 제공)

### 추가 패키지
- 없음 (기존 langchain-openai 활용)
