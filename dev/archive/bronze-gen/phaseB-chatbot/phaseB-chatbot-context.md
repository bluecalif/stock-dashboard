# Phase B: Chatbot — Context
> Last Updated: 2026-03-12
> Status: Complete

## 1. 핵심 파일

### Backend (수정/생성)
| 파일 | 용도 | 상태 |
|------|------|------|
| `backend/config/settings.py` | openai_api_key, llm_pro/lite_model | 수정 |
| `backend/api/services/llm/graph.py` | StateGraph (agent→tools, deep_mode) | 신규 |
| `backend/api/services/llm/tools.py` | 5개 Tool (DB 조회) | 신규 |
| `backend/api/services/llm/prompts.py` | 한국어 시스템 프롬프트 | 신규 |
| `backend/db/models.py` | ChatSession, ChatMessage 모델 | 수정 |
| `backend/api/schemas/chat.py` | 요청/응답 스키마 (deep_mode 포함) | 신규 |
| `backend/api/repositories/chat_repo.py` | 세션/메시지 CRUD | 신규 |
| `backend/api/services/chat/chat_service.py` | LangGraph → SSE 오케스트레이션 | 신규 |
| `backend/api/routers/chat.py` | 4 chat endpoints | 신규 |
| `backend/api/main.py` | chat 라우터 등록 | 수정 |
| `backend/pyproject.toml` | langchain-openai 의존성 | 수정 |
| `backend/.env.example` | OPENAI_API_KEY, LLM_*_MODEL | 수정 |

### Frontend (수정/생성)
| 파일 | 용도 | 상태 |
|------|------|------|
| `frontend/src/types/chat.ts` | ChatSession, ChatMessage 타입 | 신규 |
| `frontend/src/api/chat.ts` | API 함수 (deep_mode 전달) | 신규 |
| `frontend/src/hooks/useSSE.ts` | fetch + ReadableStream SSE | 신규 |
| `frontend/src/store/chatStore.ts` | Zustand (deepMode 포함) | 신규 |
| `frontend/src/components/chat/ChatPanel.tsx` | 우측 슬라이드 패널 | 신규 |
| `frontend/src/components/chat/MessageBubble.tsx` | 메시지 버블 | 신규 |
| `frontend/src/components/chat/ChatInput.tsx` | 입력 + 심층모드 토글 | 신규 |
| `frontend/src/components/layout/Layout.tsx` | ChatPanel 통합 (💬 버튼) | 수정 |

### 기타
| 파일 | 용도 | 상태 |
|------|------|------|
| `.claude/skills/langgraph-dev/SKILL.md` | Gemini → OpenAI 가이드 | 수정 |
| `db/alembic/versions/xxx_add_chat_tables.py` | chat 테이블 migration | 신규 |

## 2. 주요 결정사항

| 결정 | 선택 | 대안 | 근거 |
|------|------|------|------|
| LLM 프레임워크 | LangGraph | 직접 구현 | 명시적 그래프, SSE 이벤트 분리, checkpointer |
| LLM 모델 | OpenAI GPT-5 / GPT-5 Mini | Gemini | Gemini 쿼타 초과 (429), 결제 불가 |
| 심층모드 | 토글 (기본 Mini, 선택 Pro) | 고정 모델 | 비용 절약 + 필요시 정밀 분석 |
| 스트리밍 | SSE (StreamingResponse) | WebSocket | HTTP 호환, 구현 간편 |
| SSE 클라이언트 | fetch + ReadableStream | EventSource | POST 지원 필요 |
| Checkpointer | MemorySaver (dev) | PostgresSaver | Phase E에서 전환 |
| Chat UI | 우측 슬라이드 패널 | 별도 페이지 | 기존 대시보드 동시 사용 |
| Tool DB 접근 | 별도 세션 생성 | DI 세션 공유 | Tool은 DI 컨텍스트 밖 |

## 3. 디버깅 이력 요약

| Bug | 원인 | 수정 |
|-----|------|------|
| ToolMessage JSON 직렬화 에러 | langchain-core 1.x에서 on_tool_end output이 ToolMessage 객체로 변경 | `.content` 속성 추출 (`689dedf`) |
| Vercel ChatPanel 미표시 | `stopStream` unused 변수로 tsc 빌드 실패 | 변수 제거 (`2f21d0d`) |
| Gemini 429 쿼타 초과 | 무료 티어 한도 초과 | OpenAI GPT-5로 전환 (`807c33f`) |
| OpenAI 429 insufficient_quota | Test2 키 크레딧 소진 | book-process 키로 교체 |

## 4. 컨벤션 체크리스트

- [x] SSE 이벤트: `data: {json}\n\n` 포맷 (text_delta, tool_call, tool_result, done)
- [x] LangGraph Tool: DB 조회만 수행, LLM 직접 호출 금지
- [x] Tool 반환값: 문자열 (JSON serialize)
- [x] Tool 내 DB 세션: `next(_get_db())` 패턴
- [x] chat 엔드포인트: 인증 필수 (`get_current_user`)
- [x] 세션 소유권: `user_id` 검증
- [x] 시스템 프롬프트: 한국어, 데이터 근거 기반 응답 강제
- [x] Zustand chatStore: authStore와 분리
- [x] 심층모드: deep_mode 파라미터 Backend→Frontend 전달
