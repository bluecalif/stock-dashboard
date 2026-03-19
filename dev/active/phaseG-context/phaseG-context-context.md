# Phase G: User Context & Guided Experience — Context
> Last Updated: 2026-03-19
> Status: In Progress (G-1 ✅, G-2 ✅)

## 1. 핵심 파일

### 수정 대상 (12개)
| 파일 | 변경 내용 |
|------|----------|
| `backend/db/models.py` | UserProfile, UserActivity, ConversationSummary 모델 추가 (249줄 → ~300줄) |
| `backend/api/main.py` | `profile.router` 등록 (line 105 뒤) |
| `backend/api/services/chat/chat_service.py` | activity tracking, 요약 트리거, user_context 파이프, unsupported (492줄 → ~560줄) |
| `backend/api/repositories/chat_repo.py` | summary CRUD 추가 (81줄 → ~110줄) |
| `backend/api/services/llm/agentic/classifier.py` | user_context 파라미터 추가 (119줄) |
| `backend/api/services/llm/agentic/reporter.py` | user_context 파라미터 추가 (138줄) |
| `backend/api/services/llm/agentic/knowledge_prompts.py` | 동적 프롬프트 함수 전환 (178줄 → ~220줄) |
| `backend/api/services/llm/agentic/schemas.py` | "unsupported" Category 추가 (136줄) |
| `backend/api/routers/chat.py` | nudge-questions에 user_context 전달 (90줄) |
| `frontend/src/App.tsx` | IceBreaking 모달 + usePageTracking (42줄 → ~60줄) |
| `frontend/src/components/layout/Layout.tsx` | PageGuide 렌더링 |
| `frontend/src/components/chat/ChatPanel.tsx` | profileStore 연동 (간접적) |

### 생성 대상 (13개)
| 파일 | 용도 |
|------|------|
| `backend/db/alembic/versions/xxxx_add_user_profile_activity.py` | 마이그레이션 (G-1) |
| `backend/db/alembic/versions/xxxx_add_conversation_summaries.py` | 마이그레이션 (G-2) |
| `backend/api/repositories/profile_repo.py` | Profile/Activity CRUD |
| `backend/api/schemas/profile.py` | Pydantic 스키마 |
| `backend/api/routers/profile.py` | Profile API (4 endpoints) |
| `backend/api/services/chat/summarizer.py` | LLM 세션 요약 |
| `backend/api/services/chat/user_context.py` | UserContext 빌더 |
| `frontend/src/components/onboarding/IceBreakingModal.tsx` | 2문항 모달 |
| `frontend/src/components/onboarding/PageGuide.tsx` | 첫 방문 안내 |
| `frontend/src/api/profile.ts` | API 클라이언트 |
| `frontend/src/types/profile.ts` | TypeScript 타입 |
| `frontend/src/store/profileStore.ts` | Zustand 스토어 |
| `frontend/src/hooks/usePageTracking.ts` | 페이지 방문 추적 |

### 참조 파일 (읽기만)
| 파일 | 참조 이유 |
|------|----------|
| `backend/api/repositories/chat_repo.py` | Repository 패턴 참고 |
| `backend/api/routers/auth.py` | Router 패턴 참고 (JWT DI) |
| `backend/api/schemas/auth.py` | Pydantic 스키마 패턴 참고 |
| `backend/api/dependencies.py` | `get_current_user` DI 패턴 |
| `frontend/src/store/authStore.ts` | Zustand store 패턴 참고 |
| `frontend/src/components/auth/ProtectedRoute.tsx` | 인증 후 로직 삽입 지점 |

## 2. 데이터 인터페이스

### 입력 (어디서 읽는가)
| 데이터 | 소스 | 용도 |
|--------|------|------|
| 사용자 프로필 | `user_profiles` 테이블 | Classifier/Reporter 프롬프트 주입 |
| 사용자 활동 | `user_activity` 테이블 (JSONB) | 동적 nudge, page guide 조건 |
| 최근 세션 요약 | `conversation_summaries` 테이블 | "이전 대화 맥락" 프롬프트 주입 |
| 채팅 메시지 | `chat_messages` 테이블 | 5턴마다 요약 입력 |

### 출력 (어디에 쓰는가)
| 데이터 | 대상 | 트리거 |
|--------|------|--------|
| Ice-breaking 답변 | `user_profiles` | POST /v1/profile/ice-breaking |
| 페이지 방문 카운터 | `user_activity.activity_data` | POST /v1/profile/activity/page-visit |
| 질문 카테고리 카운터 | `user_activity.activity_data` | stream_chat 내 (자동) |
| 세션 요약 | `conversation_summaries` | 5턴마다 (asyncio.create_task) |
| top_assets/categories | `user_profiles` | 요약 생성 시 함께 갱신 |

### DB 스키마 (신규 3개 테이블)

```
user_profiles
├── user_id (UUID, PK, FK→users.id CASCADE)
├── experience_level (String(20), nullable) — beginner|intermediate|expert
├── decision_style (String(20), nullable) — feeling|logic|balanced
├── onboarding_completed (Boolean, default=False)
├── ice_breaking_raw (JSON, nullable)
├── preferred_depth (String(20), default="brief")
├── top_assets (JSON, nullable)
├── top_categories (JSON, nullable)
└── updated_at (DateTime, auto)

user_activity
├── user_id (UUID, PK, FK→users.id CASCADE)
├── activity_data (JSON, default={})
│   ├── page_visits: {page_id: count}
│   ├── asset_views: {asset_id: count}
│   ├── question_categories: {category: count}
│   ├── last_page_visit: {page_id: timestamp}
│   ├── session_count: int
│   ├── total_questions: int
│   ├── deep_mode_count: int
│   └── total_chat_count: int
└── updated_at (DateTime, auto)

conversation_summaries
├── session_id (UUID, PK, FK→chat_sessions.id CASCADE)
├── summary_data (JSON)
│   ├── turn_count: int
│   ├── categories_used: list[str]
│   ├── assets_discussed: list[str]
│   ├── key_findings: list[str]
│   └── user_intent: str
└── updated_at (DateTime, auto)
```

### API 엔드포인트 (신규 4개)

| Method | Path | Auth | 설명 |
|--------|------|------|------|
| GET | `/v1/profile` | Required | 현재 사용자 프로필 |
| POST | `/v1/profile/ice-breaking` | Required | 아이스브레이킹 답변 제출 |
| GET | `/v1/profile/activity` | Required | 활동 데이터 |
| POST | `/v1/profile/activity/page-visit` | Required | 페이지 방문 기록 |

## 3. 주요 결정사항

| 결정 | 근거 |
|------|------|
| Phase G+H 통합 | H(Onboarding)는 G(Memory)가 선행 조건. 별도 Phase로 나누면 스키마 변경 필요 |
| pgvector 미사용 | 7자산×5페이지 한정 도메인에서 구조화 쿼리가 더 정확/빠름 |
| JSONB 집계 (1 row/user) | 이벤트 로그 테이블은 현 규모에서 과도. 카운터 increment로 충분 |
| Ice-breaking 2문항 | 첫 로그인 마찰 최소화. 이후 행동 기반 progressive profiling |
| gpt-4o-mini 요약 | 비용 최적화. 분류/보고서가 아닌 요약은 경량 모델로 충분 |
| Lazy creation | 기존 users 대상 data migration 불필요. 첫 접근 시 UPSERT |
| 모든 파라미터 default=None | 기존 808 테스트 하위 호환 보장 |
| done SSE 후 요약 | 사용자 응답 지연 없이 백그라운드 실행 |

## 4. Ice-breaking 반영 지점

| 반영 지점 | 방식 |
|-----------|------|
| **Classifier 프롬프트** | experience_level → 라우팅 조정 (beginner: 기본 카테고리 우선, expert: 전략/지표 우선) |
| **Reporter 프롬프트** | experience_level + decision_style → 톤/깊이 조정 |
| **Nudge questions** | experience_level + top_assets → 동적 질문 생성 |
| **Page guide** | experience_level=beginner + 첫 방문 → 안내 메시지 |
| **Follow-up 생성** | Reporter가 experience_level 참조하여 탐색적(beginner) vs 심화(expert) |

## 5. 컨벤션 체크리스트

- [x] Router → Service → Repository 3계층 패턴
- [x] Pydantic 스키마 정의 (Request/Response)
- [x] FastAPI DI (`get_current_user`)
- [x] Alembic 마이그레이션 (새 테이블)
- [x] JSONB 원자적 연산 (카운터 증가)
- [x] 하위 호환 (default=None)
- [x] 인코딩: utf-8 explicit
- [x] 테스트: 기존 808개 + 신규 26개 = 834개
- [x] Zustand store 패턴 (프론트)
- [x] SSE 이벤트 포맷 유지
