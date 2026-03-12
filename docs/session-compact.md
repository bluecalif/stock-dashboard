# Session Compact

> Generated: 2026-03-12
> Source: Phase B Chatbot 완료

## Goal
Phase B (Chatbot) 완료 → Phase C 준비

## Completed
- [x] Phase B 전체 완료 (19/19 tasks)
- [x] B.1~B.4: Backend LLM (settings, graph, tools, prompts) → `936bc9a`
- [x] B.5~B.7: Chat DB + 스키마 + Repository → `e73096a`
- [x] B.8~B.10: Chat Service + Router + main.py → `fa112e6`
- [x] B.11~B.12: 단위 테스트 14건 + regression 440 passed → `3d8dcd7`
- [x] B.13~B.17: Frontend Chat UI → `5db4127`
- [x] B.18: LLM Gemini → OpenAI 전환 + E2E 검증 → `807c33f`, `689dedf`, `2f21d0d`
- [x] B.19: 심층모드 토글 + dev-docs 갱신 → `2202455`
- [x] Railway OPENAI_API_KEY (book-process) 설정 완료
- [x] Vercel 프론트엔드 배포 완료 (ChatPanel + 심층모드)

## Current State

### Git 상태
- 최신 커밋: `2202455` (master, origin 동기화 완료)

### 인프라 상태
- **Railway**: backend + Postgres, OPENAI_API_KEY 설정 완료
  - 공개 URL: `https://backend-production-e5bc.up.railway.app`
- **Vercel**: `https://stock-dashboard-alpha-lilac.vercel.app`

### 테스트 상태
- Backend: 440 passed, 7 skipped, ruff clean
- Frontend: TypeScript 0 errors, Vite build 성공

### OpenAI API Key
- `.env` 파일에 설정 완료 (커밋 제외)
- 키 파일: `C:\Users\User\Work\AI-Engine\각종 API Key_REV0.csv` (line 10, book-process)

## Key Decisions
- passlib 제거 → bcrypt 직접 사용 (Phase A)
- **Gemini → OpenAI GPT-5 전환**: Gemini 쿼타 초과 (429) + 결제 문제
- 모델: `gpt-5` (심층모드), `gpt-5-mini` (기본) — 심층모드 토글
- LangGraph 유지 (프레임워크 변경 없음, LLM만 교체)
- SSE: fetch + ReadableStream (EventSource GET 제한)
- Chat UI: 우측 슬라이드 패널 (기존 대시보드 유지)
- langchain-core 1.x ToolMessage 직렬화 수정

## Context
- 다음 세션에서는 답변에 한국어를 사용하세요.
- **기존 코드 패턴**: Router-Service-Repository 3계층, 함수형 repo, Pydantic v2, SQLAlchemy 2.0 Mapped
- **Railway**: 프로젝트 `stock-dashboard`, CLI 인증 만료 (대시보드에서 직접 설정)
- **Frontend**: React 19 + Vite + TypeScript + Tailwind + axios + react-router-dom v6 + zustand
- **LangGraph**: langgraph 1.1.1 + langchain-openai 1.1.11 + langchain-core 1.2.18
- **SSE 주의**: EventSource(GET) 사용 금지 → fetch + ReadableStream 사용
- **Tool DB 접근**: DI 밖이므로 `next(_get_db())` 패턴 사용

## Project Status

| Phase | 상태 | 비고 |
|-------|------|------|
| MVP (0~7) | ✅ 완료 | 83/83 tasks |
| Post-MVP 기획 | ✅ 완료 | 기술 결정 + 플랜 |
| Phase A Auth | ✅ 완료 | 16/16 tasks |
| Phase B Chatbot | ✅ 완료 | 19/19 tasks |
| Phase C~F | ⬜ 미시작 | |

## Next Action
1. Phase C 기획 (`/dev-docs`로 상세 계획)
2. 분석 시나리오 API 구현
