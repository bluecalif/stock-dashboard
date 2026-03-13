# Session Compact

> Generated: 2026-03-13
> Source: Phase C 구현 진행 중 (C.1~C.7 완료, C.8 시작 직전)

## Goal
Phase C (상관도 페이지 완성) 12 Steps 구현 — Backend 분석 서비스 + LangGraph Tool + 하이브리드 응답 + Frontend 확장

## Completed
- [x] Phase C~E 통합 검증 단계 추가 (C.12, D.12, E.10)
- [x] C.1 상관도 분석 서비스 — `correlation_analysis.py` (Union-Find 그룹핑, top pairs, 유사자산) — `3cf57f7`
- [x] C.2 스프레드 분석 서비스 — `spread_service.py` (정규화 가격 비율 + z-score 수렴/발산) — `21e0b52`
- [x] C.3 해석 규칙 상수 — `interpretation_rules.py` (상관도/z-score 한국어 해석) — `21e0b52`
- [x] C.4 LangGraph Tool — `analyze_correlation_tool` (그룹핑+TOP쌍+유사자산+해석 JSON) — `e1d9e40`
- [x] C.5 LangGraph Tool — `get_spread` (z-score+수렴이벤트+해석 JSON) — `e1d9e40`
- [x] C.6 하이브리드 응답 기반 — `hybrid/` 디렉토리 (classifier, templates, actions, context) — `2caf0d4`
- [x] C.7 하이브리드 → LangGraph 통합 — chat_service 하이브리드 경로 + LLM fallback + ui_action SSE

## Current State

### Git 상태
- 최신 커밋: C.7 커밋 (push 후 갱신)
- 변경: 없음 (커밋 후)

### 테스트 상태
- 전체: **561 tests** passed (신규 16 + 기존 545)
- ruff clean

### 인프라 상태
- **Railway**: backend + Postgres, OPENAI_API_KEY 설정 완료
  - 공개 URL: `https://backend-production-e5bc.up.railway.app`
- **Vercel**: `https://stock-dashboard-alpha-lilac.vercel.app`

### OpenAI API Key
- `.env` 파일에 설정 완료 (커밋 제외)
- 키 파일: `C:\Users\User\Work\AI-Engine\각종 API Key_REV0.csv` (line 10, book-process)

### 생성된 파일 (C.7)
- `backend/tests/unit/test_hybrid_integration.py`

### 수정된 파일 (C.7)
- `backend/api/schemas/chat.py` — `PageContextRequest` 스키마 추가
- `backend/api/routers/chat.py` — `page_context` 전달
- `backend/api/services/chat/chat_service.py` — 하이브리드 분류기 통합 + ui_action SSE
- `backend/api/services/llm/graph.py` — `_build_system_prompt()` + page_context 반영

## Remaining / TODO
- [x] C.7 하이브리드를 LangGraph에 통합 `[L]` ✅
- [ ] C.8 SSE 확장 + chartActionStore `[M]`
- [ ] C.9 상관도 페이지 확장 (그룹핑+Scatter) `[M]`
- [ ] C.10 SpreadChart + 넛지 질문 UI `[M]`
- [ ] C.11 관심 종목 설정 `[S]`
- [ ] C.12 Phase C 통합 검증 `[M]`
- [ ] Phase D 구현 (D.1~D.12)
- [ ] Phase E 구현 (E.1~E.10)

### Phase C: 상관도 페이지 (12 Steps)
| Step | 내용 | 상태 | 커밋 |
|------|------|------|------|
| C.1 | 상관도 분석 서비스 (그룹핑/유사자산) | ✅ | `3cf57f7` |
| C.2 | 스프레드 분석 서비스 | ✅ | `21e0b52` |
| C.3 | 해석 규칙 상수 | ✅ | `21e0b52` |
| C.4 | Tool: analyze_correlation | ✅ | `e1d9e40` |
| C.5 | Tool: get_spread | ✅ | `e1d9e40` |
| C.6 | 하이브리드 응답 기반 | ✅ | `2caf0d4` |
| C.7 | 하이브리드 → LangGraph 통합 | ✅ | (커밋 후 갱신) |
| C.8 | SSE 확장 + chartActionStore | ⬜ | - |
| C.9 | 상관도 페이지 확장 | ⬜ | - |
| C.10 | SpreadChart + 넛지 질문 | ⬜ | - |
| C.11 | 관심 종목 설정 | ⬜ | - |
| C.12 | 통합 검증 | ⬜ | - |

## Key Decisions
- passlib 제거 → bcrypt 직접 사용 (Phase A)
- **Gemini → OpenAI GPT-5 전환**: Gemini 쿼타 초과 (429) + 결제 문제
- 모델: `gpt-5` (심층모드), `gpt-5-mini` (기본) — 심층모드 토글
- LangGraph 유지 (프레임워크 변경 없음, LLM만 교체)
- SSE: fetch + ReadableStream (EventSource GET 제한)
- Chat UI: 우측 슬라이드 패널 (기존 대시보드 유지)
- **Phase C~E 설계 결정**:
  - 하이브리드 분류기 = 정규표현식+키워드 (LLM intent 안 씀)
  - 분류 실패 시 LangGraph LLM fallback
  - 스토리텔링 = 하드코딩 템플릿+f-string
  - on-the-fly 경량 백테스트 (DB 저장 안 함)
- **통합 검증 단계 추가**: 각 Phase 마지막에 Backend+Frontend+E2E 검증 step 필수
- **해석 규칙 경계값**: 음수 상관계수는 reversed 순서로 매칭 (극단값 우선)
- **C.7 하이브리드 통합**: chat_service에서 분류기 호출 → 템플릿 응답 or LangGraph fallback (graph.py 노드 추가 아님)

## Context
- 다음 세션에서는 답변에 한국어를 사용하세요.
- **통합 계획 파일**: `docs/post-mvp-phaseCD-detail.md`
- **기존 코드 패턴**: Router-Service-Repository 3계층, 함수형 repo, Pydantic v2, SQLAlchemy 2.0 Mapped
- **Railway**: 프로젝트 `stock-dashboard`, CLI 인증 만료 (대시보드에서 직접 설정)
- **Frontend**: React 19 + Vite + TypeScript + Tailwind + axios + react-router-dom v6 + zustand
- **LangGraph**: langgraph 1.1.1 + langchain-openai 1.1.11 + langchain-core 1.2.18
- **SSE 주의**: EventSource(GET) 사용 금지 → fetch + ReadableStream 사용
- **Tool DB 접근**: DI 밖이므로 `next(_get_db())` 패턴 사용
- **C.8 SSE 확장 핵심 파일** (다음에 읽어야 할 것):
  - `frontend/src/types/chat.ts` — SSEEvent에 `ui_action` 타입 추가
  - `frontend/src/hooks/useSSE.ts` — `onUIAction` 콜백 추가
  - `frontend/src/api/chat.ts` — `sendMessageSSE`에 pageContext 파라미터
  - `frontend/src/components/chat/ChatPanel.tsx` — 페이지 컨텍스트 전송

## Project Status

| Phase | 상태 | 비고 |
|-------|------|------|
| MVP (0~7) | ✅ 완료 | 83/83 tasks |
| Post-MVP 기획 | ✅ 완료 | 기술 결정 + 플랜 |
| Phase A Auth | ✅ 완료 | 16/16 tasks |
| Phase B Chatbot | ✅ 완료 | 19/19 tasks |
| Phase C 상관도 | 🔄 진행 중 | 7/12 Steps (58%) |
| Phase D 지표 | ⬜ 미시작 | 12 Steps |
| Phase E 전략 | ⬜ 미시작 | 10 Steps |
| Phase F~G | ⬜ 미시작 | Memory/Onboarding |

## Next Action
1. **C.8 SSE 확장 + chartActionStore** 구현
   - Frontend `types/chat.ts`에 `ui_action` SSE 이벤트 타입 추가
   - `hooks/useSSE.ts`에 `onUIAction` 콜백 추가
   - `store/chartActionStore.ts` 신규 (Zustand)
   - `api/chat.ts` — `sendMessageSSE`에 pageContext 추가
   - `ChatPanel.tsx` — 페이지 컨텍스트 전송
2. 이후 C.9~C.12 순차 진행
