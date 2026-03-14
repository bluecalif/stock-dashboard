# Session Compact

> Generated: 2026-03-14
> Source: Phase C-rev 프로덕션 리뷰 피드백 (2차)

## Goal
Phase C-rev 프로덕션 배포 후 브라우저 리뷰 → 추가 피드백 3건 수집 및 분석 완료. 구현은 아직 미시작.

## Completed
- [x] Phase C-rev 7/7 Tasks 완료 및 프로덕션 배포 (이전 세션)
- [x] 프로덕션 브라우저 리뷰 — 사용자 피드백 3건 수집
- [x] 피드백 분석 및 개선 방향 논의 완료

## Current State

### Git 상태
- 최신 커밋: `d7f7a8c` (master, push 완료)
- 미커밋 변경: dev-docs 이전 세션 파일들

### 테스트 상태
- 전체: **561 tests** passed, 7 skipped
- ruff/tsc/vite build clean

### 인프라 상태
- **Railway**: `https://backend-production-e5bc.up.railway.app`
- **Vercel**: `https://stock-dashboard-alpha-lilac.vercel.app`

## Remaining / TODO — Phase C-rev2 (피드백 3건)

### 피드백 1: 히트맵 셀 클릭 → Scatter Plot 추가
- **현재**: 히트맵 셀 클릭 → Spread Chart (정규화 가격 + Z-score) 로드
- **원하는 것**: X축=종목A 일별 수익률, Y축=종목B 일별 수익률 **산점도(scatter plot)** 표시
- **합의된 방향**: B안 — scatter plot을 **추가** (3-패널: scatter + 정규화 가격 + Z-score)
- **구현 필요**:
  - Backend: 일별 수익률 데이터 API (또는 기존 데이터에서 계산)
  - Frontend: ScatterPlotChart 새로 구현 (수익률 기반 X-Y 산점도)

### 피드백 2: 넛지 칩 상시 표시
- **현재**: 넛지 칩 클릭 → 답변 후 칩 사라짐
- **원하는 것**: 답변 후에도 채팅 상단에 넛지 칩 항상 표시
- **구현**: 프론트 UI 변경만 필요

### 피드백 3: 질문 분류 전략 개선
- **현재 문제**: `classify_question()`이 regex 기반으로 매칭/불매칭만 판단 (confidence 없음)
  - regex 매칭 성공 → 무조건 템플릿 응답 (is_nudge 여부 무관)
  - 사용자 직접 질문도 regex 매칭되면 템플릿 응답 → 의도와 불일치 가능
- **현재 흐름**:
  ```
  classify_question(regex) → 카테고리?
    ├─ Yes → 데이터 fetch → 템플릿 응답
    ├─ No + is_nudge=True → 페이지별 기본 카테고리 강제 → 템플릿 응답
    └─ No + is_nudge=False → LangGraph LLM fallback
  ```
- **합의된 개선 방향**: is_nudge=False (사용자 직접 질문)면 **항상 LLM fallback**으로 보내기
  - 템플릿은 넛지 전용으로만 사용
  - 또는 regex confidence 개념 도입 검토
- **관련 파일**:
  - `backend/api/services/chat/chat_service.py` — stream_chat() 분기 로직
  - `backend/api/services/llm/hybrid/classifier.py` — classify_question() regex 패턴

### 기존 TODO
- [ ] Phase D 구현 (D.1~D.11) — 지표 페이지 완성
- [ ] Phase E 구현 (E.1~E.9) — 전략 페이지 완성

## Key Decisions
- **Scatter Plot**: 교체(A안)가 아닌 추가(B안) — 정보량 유지
- **질문 분류**: is_nudge=True → 템플릿, is_nudge=False → LLM (가장 간단한 접근)
- **넛지 칩**: 항상 상단에 표시 유지

## Context
- 다음 세션에서는 답변에 한국어를 사용하세요.
- **기존 코드 패턴**: Router-Service-Repository 3계층, 함수형 repo, Pydantic v2, SQLAlchemy 2.0 Mapped
- **Frontend**: React 19 + Vite + TypeScript + Tailwind + axios + react-router-dom v6 + zustand + Recharts
- **LangGraph**: langgraph 1.1.1 + langchain-openai 1.1.11 + langchain-core 1.2.18
- **SSE 주의**: EventSource(GET) 사용 금지 → fetch + ReadableStream 사용
- **LangSmith API Key**: (환경변수 참조)

## Project Status

| Phase | 상태 | 비고 |
|-------|------|------|
| MVP (0~7) | ✅ 완료 | 83/83 tasks |
| Phase A Auth | ✅ 완료 | 16/16 tasks |
| Phase B Chatbot | ✅ 완료 | 19/19 tasks |
| Phase C 상관도 | ✅ 완료 | 12/12 Steps |
| Phase C-rev 피드백 | ✅ 완료 | 7/7 Tasks |
| Phase C-rev2 피드백 | ✅ 완료 | 4/4 Tasks |
| Phase D 지표 | ⬜ 미시작 | 11 Steps |
| Phase E 전략 | ⬜ 미시작 | 9 Steps |
| Phase F~G | ⬜ 미시작 | Memory/Onboarding |

## Next Action
1. **Phase C-rev2 구현** — `/dev-docs`로 상세 계획 수립 후 3건 피드백 구현
   - 피드백 1: scatter plot 추가 (백엔드 수익률 API + 프론트 차트)
   - 피드백 2: 넛지 칩 상시 표시 (프론트 UI)
   - 피드백 3: 질문 분류 전략 개선 (백엔드 chat_service)
