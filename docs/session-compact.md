# Session Compact

> Generated: 2026-03-13
> Source: Phase C 완료 (C.1~C.12 전체 완료)

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
- [x] C.7 하이브리드 → LangGraph 통합 — chat_service 하이브리드 경로 + LLM fallback + ui_action SSE — `4e2c15c`
- [x] C.8 SSE 확장 + chartActionStore — `09fe91e`
- [x] C.9 상관도 페이지 확장 (그룹핑+Scatter) — `edf759e`
- [x] C.10 SpreadChart + 넛지 질문 UI — `17c4742`
  - `GET /v1/correlation/spread` 엔드포인트 (z-score + 수렴/발산 이벤트)
  - `GET /v1/chat/nudge-questions` 엔드포인트 (페이지별 추천 질문)
  - SpreadChart 컴포넌트 (z-score 라인차트 + ±1σ/±2σ 밴드 + 이벤트 태그)
  - NudgeQuestions 컴포넌트 (ChatPanel 빈 상태에서 추천 질문 칩)
- [x] C.11 관심 종목 설정 — `17c16a7`
  - CorrelationPage에 AssetSelect 멀티 선택 필터
- [x] C.12 Phase C 통합 검증 — ruff/pytest/tsc/vite build/E2E API 전체 통과

## Current State

### Git 상태
- 최신 커밋: `17c16a7` (C.11)
- Phase C 전체 완료, push 필요

### 테스트 상태
- 전체: **561 tests** passed, 7 skipped
- ruff clean, tsc clean, vite build 성공
- E2E API 검증: correlation, analysis, spread, filtered — 모두 정상

### 인프라 상태
- **Railway**: backend + Postgres, OPENAI_API_KEY 설정 완료
  - 공개 URL: `https://backend-production-e5bc.up.railway.app`
- **Vercel**: `https://stock-dashboard-alpha-lilac.vercel.app`

### OpenAI API Key
- `.env` 파일에 설정 완료 (커밋 제외)
- 키 파일: `C:\Users\User\Work\AI-Engine\각종 API Key_REV0.csv` (line 10, book-process)

## Phase C: 상관도 페이지 (12 Steps) — ✅ 완료
| Step | 내용 | 상태 | 커밋 |
|------|------|------|------|
| C.1 | 상관도 분석 서비스 (그룹핑/유사자산) | ✅ | `3cf57f7` |
| C.2 | 스프레드 분석 서비스 | ✅ | `21e0b52` |
| C.3 | 해석 규칙 상수 | ✅ | `21e0b52` |
| C.4 | Tool: analyze_correlation | ✅ | `e1d9e40` |
| C.5 | Tool: get_spread | ✅ | `e1d9e40` |
| C.6 | 하이브리드 응답 기반 | ✅ | `2caf0d4` |
| C.7 | 하이브리드 → LangGraph 통합 | ✅ | `4e2c15c` |
| C.8 | SSE 확장 + chartActionStore | ✅ | `09fe91e` |
| C.9 | 상관도 페이지 확장 (그룹핑+Scatter) | ✅ | `edf759e` |
| C.10 | SpreadChart + 넛지 질문 | ✅ | `17c4742` |
| C.11 | 관심 종목 설정 | ✅ | `17c16a7` |
| C.12 | 통합 검증 | ✅ | — |

## Remaining / TODO
- [ ] Phase D 구현 (D.1~D.11)
- [ ] Phase E 구현 (E.1~E.9)

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
- **C.7 하이브리드 통합**: chat_service에서 분류기 호출 → 템플릿 응답 or LangGraph fallback
- **C.9 API 설계**: `/v1/correlation/analysis` 엔드포인트 — correlation_service → correlation_analysis.py
- **C.10 SpreadChart**: z-score ±1σ/±2σ 밴드 + 수렴/발산 이벤트 태그 + 페어 선택 시 자동 로딩

## Context
- 다음 세션에서는 답변에 한국어를 사용하세요.
- **통합 계획 파일**: `docs/post-mvp-phaseCD-detail.md`
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
| Phase C 상관도 | ✅ 완료 | 12/12 Steps |
| Phase D 지표 | ⬜ 미시작 | 11 Steps |
| Phase E 전략 | ⬜ 미시작 | 9 Steps |
| Phase F~G | ⬜ 미시작 | Memory/Onboarding |

## Next Action
1. **Phase D 시작** — D.1 지표 분석 서비스 (현재 상태 해석)
