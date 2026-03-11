# Session Compact

> Generated: 2026-03-10 23:50
> Source: Conversation compaction via /compact-and-go

## Goal
Post-MVP 제품 구현 계획 수립 — MVP(읽기 전용 대시보드)를 대화형 분석 워크스페이스로 확장하기 위한 아키텍처 설계, 기술 결정, 스킬 업데이트.

## Completed
- [x] `docs/post-mvp-implementation-sketch.md` 리뷰 및 누락 항목 식별
- [x] 현재 코드베이스 전수 탐색 (백엔드 8 라우터/8 테이블, 프론트엔드 6 페이지)
- [x] 핵심 기술 결정 확정 (Auth, LLM, Chat, State, Embedding, Vector DB)
- [x] LangChain vs LangGraph 비교 분석 → LangGraph 채택
- [x] LLM 모델: OpenAI → Claude → **Gemini** 최종 변경
- [x] 6개 Phase 구현 계획 작성 (A~F)
- [x] `langgraph-dev` skill 신규 생성
- [x] `backend-dev` skill 업데이트 (Auth 패턴 추가)
- [x] `frontend-dev` skill 업데이트 (Zustand, SSE, ProtectedRoute 추가)
- [x] `skill-rules.json` 업데이트 (langgraph-dev 등록, 키워드 확장)

## Current State

### Git 상태
- 최신 커밋: `5e866dc` (master)
- 미커밋 변경:
  - `.claude/settings.local.json` — 세션 설정
  - `docs/post-mvp-draft.md` — 수정
  - `docs/post-mvp-implementation-sketch.md` — 신규 (미추적)
  - `.claude/skills/langgraph-dev/SKILL.md` — 신규
  - `.claude/skills/backend-dev/SKILL.md` — 수정
  - `.claude/skills/frontend-dev/SKILL.md` — 수정
  - `.claude/skills/skill-rules.json` — 수정
  - `.claude/plans/snuggly-growing-willow.md` — 플랜 파일

### Changed Files
- `.claude/skills/langgraph-dev/SKILL.md` — 신규: LangGraph + Gemini 에이전트 가이드
- `.claude/skills/backend-dev/SKILL.md` — Auth 패턴 (JWT, get_current_user) 추가
- `.claude/skills/frontend-dev/SKILL.md` — Zustand store, SSE 훅, ProtectedRoute 패턴 추가
- `.claude/skills/skill-rules.json` — langgraph-dev 등록 + Gemini/auth/Zustand 키워드 추가
- `.claude/plans/snuggly-growing-willow.md` — Post-MVP 전체 구현 계획

### 인프라 상태
- **Railway**: backend + Postgres 운영 중
  - 공개 URL: `https://backend-production-e5bc.up.railway.app`
  - Public Networking: `mainline.proxy.rlwy.net:34025`
- **Vercel**: `https://stock-dashboard-alpha-lilac.vercel.app`
- **gh CLI**: `bluecalif` 계정, remote: `https://github.com/bluecalif/stock-dashboard.git`

## Remaining / TODO
- [ ] `/dev-docs` skill 소개 및 활용법 확인
- [ ] Post-MVP 변경사항 커밋
- [ ] Phase A (Auth) 상세 기획 (`/dev-docs`) 및 구현 착수
- [ ] Phase B~F 순차 구현

## Key Decisions

### 확정된 기술 결정
| 항목 | 결정 |
|------|------|
| Auth | JWT 자체 구현 (python-jose + passlib) |
| LLM 플랫폼 | **LangGraph** (langgraph + langchain-core + langchain-google-genai) |
| LLM 모델 | **Gemini 3.1 Pro** (메인 챗봇/분석) + **Gemini 3.1 Flash Lite** (분류/온보딩) |
| Chat 프로토콜 | SSE 스트리밍 (FastAPI StreamingResponse) |
| 상태 관리 | Zustand 추가 (기존 React hooks 유지, 공유 상태만 store) |
| Embedding | Phase E 진입 시 결정 (Gemini embedding 또는 OpenAI) |
| Vector DB | pgvector (Railway 지원 여부 Phase E 전 확인) |
| 비용 제어 | 초기 제한 없음, 토큰 사용량 컬럼 미리 설계 |

### Phase 구현 순서
```
A (Auth) → B (Chat) → C (Analysis) → D (Graph Custom) → E (Memory+Vector) → F (Onboarding)
```
- Phase A, B: 플랜에서 상세 확정
- Phase C~F: 각 Phase 진입 시 `/dev-docs` skill로 상세 기획 후 구현

### 기타 결정
- LangChain vs LangGraph 비교 → LangGraph 채택 (명시적 그래프, SSE 이벤트 분리, 내장 checkpointer)
- LLM: OpenAI → Claude → Gemini (비용 이유)
- 기존 공개 API는 auth 없이 하위 호환 유지
- Skill 구조: langgraph-dev 신규 + backend-dev/frontend-dev 업데이트 (간결하게 유지)

## Context
- 다음 세션에서는 답변에 한국어를 사용하세요.
- **플랜 파일**: `.claude/plans/snuggly-growing-willow.md` — 전체 구현 계획 참조
- **구현 스케치**: `docs/post-mvp-implementation-sketch.md` — 제품 요구사항 원본
- **Railway**: 프로젝트 `stock-dashboard`
  - 프로젝트 ID: `50fe3dfd-fc3c-495a-b1dd-e10c4cd68aac`
  - 서비스 ID: `0f64966e-c557-483e-a79e-7a385cf4ba6c`
- **Vercel**: projectId `prj_JHiNy6kA0O1AwGv0z7XRoEQKT069`

## Project Status

| Phase | 상태 | 비고 |
|-------|------|------|
| MVP (0~7) | ✅ 완료 | 83/83 tasks |
| Post-MVP 기획 | ✅ 완료 | 기술 결정 + 플랜 + 스킬 업데이트 |
| Phase A (Auth) | ⬜ 미시작 | 다음 착수 대상 |
| Phase B (Chat) | ⬜ 미시작 | |
| Phase C~F | ⬜ 미시작 | dev-docs로 상세 기획 예정 |

## Next Action
- `/dev-docs` skill 소개 확인 후, Post-MVP 변경사항 커밋
- 이후 Phase A (Auth + User Context) 상세 기획 (`/dev-docs`) 및 구현 착수
