# Phase B: Chatbot 기본 루프
> Last Updated: 2026-03-12
> Status: Complete

## 1. Summary (개요)

**목적**: LangGraph + OpenAI GPT-5 기반 대화형 분석 챗봇 구축. 사용자가 자연어로 자산/팩터/전략 데이터를 질의하고, SSE 스트리밍으로 실시간 응답을 받는 기본 대화 루프 완성.

**범위**:
- Backend LLM 계층: LangGraph StateGraph (agent→tools 루프), LangChain Tool, 시스템 프롬프트
- Backend Chat: chat_sessions/chat_messages DB, chat_service (SSE 오케스트레이션), chat router
- Frontend Chat: chatStore (Zustand), ChatPanel (슬라이드 패널), SSE 파싱, 메시지 UI
- 심층모드 토글: 기본 GPT-5 Mini (빠른 응답), 토글 시 GPT-5 (정밀 분석)
- 기존 API/페이지: 변경 없음 (채팅 패널은 레이아웃 오버레이)

**결과물**:
- 채팅 세션 생성 → 메시지 전송 → LLM이 Tool 호출 → 실시간 텍스트 응답
- Tool: 가격 조회, 팩터 조회, 상관행렬 조회, 시그널 조회, 백테스트 목록
- SSE 이벤트: text_delta, tool_call, tool_result, done
- 우측 슬라이드 채팅 패널 UI + 심층모드 토글

## 2. Current State (완료 상태)

- Phase B 전체 완료 (19/19 tasks)
- LLM: OpenAI GPT-5 (pro) / GPT-5 Mini (lite) — Gemini에서 전환
- 패키지: langchain-openai 1.1.11, langgraph 1.1.1, langchain-core 1.2.18
- Backend: 4 chat endpoints, 440 passed, ruff clean
- Frontend: ChatPanel + 심층모드 토글, TypeScript 0 errors
- Railway + Vercel 프로덕션 E2E 검증 완료
- Tests: 440 passed, 7 skipped, ruff clean

## 3. Key Changes from Original Plan

| 항목 | 원래 계획 | 실제 구현 | 근거 |
|------|----------|----------|------|
| LLM 모델 | Gemini 3.1 Pro | OpenAI GPT-5 | Gemini 무료 쿼타 초과 (429) + 결제 문제 |
| LLM 패키지 | langchain-google-genai | langchain-openai | 모델 전환에 따른 변경 |
| 설정 변수 | google_api_key, gemini_* | openai_api_key, llm_pro/lite_model | OpenAI 전환 |
| 심층모드 | 미계획 | 구현 완료 | 사용자 요청: 기본 GPT-5 Mini, 토글 GPT-5 |
| Chat endpoints | 3개 | 4개 (+GET /sessions 목록) | 세션 목록 조회 필요 |

## 4. Implementation Stages (완료)

### Stage A: Backend LLM 기반 (Step B.1~B.4) ✅
### Stage B: Backend Chat 데이터 (Step B.5~B.7) ✅
### Stage C: Backend Chat API (Step B.8~B.10) ✅
### Stage D: Backend 테스트 (Step B.11~B.12) ✅
### Stage E: Frontend Chat (Step B.13~B.17) ✅
### Stage F: E2E 검증 + 문서 (Step B.18~B.19) ✅
