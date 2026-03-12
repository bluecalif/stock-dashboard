# Session Compact

> Generated: 2026-03-12 00:00
> Source: Conversation compaction via /compact-and-go

## Goal
Phase B (Chatbot) 구현: LLM 기반 AI 분석 도우미 챗봇 (Backend + Frontend)

## Completed
- [x] B.1 Settings: google_api_key, gemini model → **OpenAI로 전환 중** (`936bc9a` + 미커밋)
- [x] B.2 LangGraph graph.py: StateGraph (agent→tools→agent 루프, MemorySaver) → `936bc9a`
- [x] B.3 tools.py: 5개 Tool (get_prices, get_factors, get_correlation, get_signals, list_backtests) → `936bc9a`
- [x] B.4 prompts.py: 한국어 분석 도우미 시스템 프롬프트 → `936bc9a`
- [x] B.5 DB 모델: ChatSession, ChatMessage + Alembic migration → `e73096a`
- [x] B.6 Pydantic 스키마: chat.py → `e73096a`
- [x] B.7 Repository: chat_repo.py → `e73096a`
- [x] B.8 Service: chat_service.py (LangGraph → SSE 오케스트레이션) → `fa112e6`
- [x] B.9 Router: chat.py (4 endpoints) → `fa112e6`
- [x] B.10 main.py 라우터 등록 + pyproject.toml 의존성 → `fa112e6`
- [x] B.11 단위 테스트: chat service + router (14건) → `3d8dcd7`
- [x] B.12 Regression: 440 passed, ruff clean → `3d8dcd7`
- [x] B.13 Frontend: types/chat.ts + api/chat.ts → `5db4127`
- [x] B.14 Frontend: hooks/useSSE.ts (fetch + ReadableStream) → `5db4127`
- [x] B.15 Frontend: store/chatStore.ts (Zustand) → `5db4127`
- [x] B.16 Frontend: ChatPanel + MessageBubble + ChatInput → `5db4127`
- [x] B.17 Frontend: Layout.tsx에 ChatPanel 통합 → `5db4127`
- [x] git push (5db4127까지 origin 동기화 완료)
- [x] E2E 부분 검증: 세션 생성/조회/목록/기존 API 정상, SSE 플로우 동작 확인

## Current State

### Git 상태
- 최신 커밋: `5db4127` (master, origin 동기화 완료)
- 미커밋 변경 (LLM 전환 작업 중단):
  - `backend/config/settings.py` — Gemini → OpenAI 설정으로 변경 (settings 변수명만 변경됨)
  - `backend/.env.example` — 아직 Gemini 상태 (업데이트 필요)
  - `backend/.env` — 아직 GOOGLE_API_KEY (OPENAI_API_KEY로 교체 필요)
  - `backend/api/services/llm/graph.py` — 아직 ChatGoogleGenerativeAI (ChatOpenAI로 교체 필요)

### LLM 전환 상태 (Gemini → OpenAI GPT-5)
**완료된 것:**
- `config/settings.py`: `openai_api_key`, `llm_pro_model="gpt-5"`, `llm_lite_model="gpt-5-mini"`

**아직 변경 필요:**
1. `backend/api/services/llm/graph.py`:
   - `from langchain_google_genai import ChatGoogleGenerativeAI` → `from langchain_openai import ChatOpenAI`
   - `_build_model()`: `ChatGoogleGenerativeAI(model=..., google_api_key=...)` → `ChatOpenAI(model=settings.llm_pro_model, api_key=settings.openai_api_key)`
2. `backend/.env`: `GOOGLE_API_KEY=...` → `OPENAI_API_KEY=sk-proj-...`
3. `backend/.env.example`: Gemini 섹션 → OpenAI 섹션
4. `backend/pyproject.toml`: `langchain-google-genai` → `langchain-openai`
5. Railway 환경변수: `GOOGLE_API_KEY` 삭제, `OPENAI_API_KEY` 추가
6. `.claude/skills/langgraph-dev/SKILL.md`: Gemini → OpenAI 가이드 업데이트

### OpenAI API Key
- `.env` 파일에 설정 완료 (커밋 제외)
- 키 파일: `C:\Users\User\Work\AI-Engine\각종 API Key_REV0.csv` (line 9)

### 인프라 상태
- **Railway**: backend + Postgres 운영 중, JWT_SECRET_KEY 설정 완료, GOOGLE_API_KEY 설정됨 (→ OPENAI_API_KEY로 교체 필요)
  - 공개 URL: `https://backend-production-e5bc.up.railway.app`
  - Railway CLI 인증 만료 — 대시보드에서 직접 설정 필요
- **Vercel**: `https://stock-dashboard-alpha-lilac.vercel.app`

### 테스트 상태
- Backend: 440 passed, 7 skipped, ruff clean
- Frontend: TypeScript 0 errors, Vite build 성공

## Remaining / TODO
- [ ] **LLM 전환 완료** (Gemini → OpenAI GPT-5) — 위 "아직 변경 필요" 6개 항목
- [ ] E2E 재검증 (OpenAI 전환 후)
- [ ] B.18 E2E 검증 완료 기록
- [ ] B.19 dev-docs 갱신 + 커밋
- [ ] Railway 환경변수 교체 (GOOGLE_API_KEY → OPENAI_API_KEY)
- [ ] 프로덕션 E2E 검증

## Key Decisions
- passlib 제거 → bcrypt 직접 사용 (Phase A)
- **Gemini → OpenAI GPT-5 전환**: Gemini 무료 티어 쿼타 초과 (429) + 결제 문제
- 모델: `gpt-5` (pro), `gpt-5-mini` (lite) — 사용자 지정
- LangGraph 유지 (프레임워크는 변경 없음, LLM만 교체)
- SSE: fetch + ReadableStream (EventSource GET 제한)
- Chat UI: 우측 슬라이드 패널 (기존 대시보드 유지)

## Context
- 다음 세션에서는 답변에 한국어를 사용하세요.
- **Phase B dev-docs**: `dev/active/phaseB-chatbot/` — plan, context, tasks, debug-history
- **기존 코드 패턴**: Router-Service-Repository 3계층, 함수형 repo, Pydantic v2, SQLAlchemy 2.0 Mapped
- **Railway**: 프로젝트 `stock-dashboard`, CLI 인증 만료 (대시보드에서 직접 설정)
- **Frontend**: React 19 + Vite + TypeScript + Tailwind + axios + react-router-dom v6 + zustand
- **LangGraph**: langgraph 1.0.3 + langgraph-prebuilt 1.0.8 — ToolNode import OK
- **패키지**: `langchain-google-genai` → `langchain-openai`로 교체 필요
- **SSE 주의**: EventSource(GET) 사용 금지 → fetch + ReadableStream 사용
- **Tool DB 접근**: DI 밖이므로 `with SessionLocal() as db:` 패턴 사용

## Project Status

| Phase | 상태 | 비고 |
|-------|------|------|
| MVP (0~7) | ✅ 완료 | 83/83 tasks |
| Post-MVP 기획 | ✅ 완료 | 기술 결정 + 플랜 |
| Phase A Auth | ✅ 완료 | 16/16 tasks |
| Phase B Chatbot | 🔄 진행중 | 17/19 tasks (LLM 전환 중) |
| Phase C~F | ⬜ 미시작 | |

## Next Action
1. **LLM Gemini → OpenAI 전환 완료** (graph.py, .env, .env.example, pyproject.toml, SKILL.md)
2. `pip install langchain-openai` + import 검증
3. E2E 로컬 검증 (OpenAI GPT-5)
4. 커밋 + push
5. Railway 환경변수 교체 (사용자에게 확인)
6. B.19 dev-docs 갱신
