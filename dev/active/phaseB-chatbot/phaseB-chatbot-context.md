# Phase B: Chatbot — Context
> Last Updated: 2026-03-12
> Status: Planning

## 1. 핵심 파일 — 이 Phase에서 읽어야 할 기존 코드

### Backend (수정 대상)
| 파일 | 용도 | 수정 내용 |
|------|------|----------|
| `backend/db/models.py` | DB 모델 (10 테이블) | ChatSession, ChatMessage 모델 추가 |
| `backend/config/settings.py` | Settings 싱글톤 | google_api_key, gemini model 설정 추가 |
| `backend/api/main.py` | 앱 엔트리포인트 | chat 라우터 등록 |
| `backend/pyproject.toml` | 의존성 | langgraph, langchain-core, langchain-google-genai |
| `backend/.env.example` | 환경변수 예시 | GOOGLE_API_KEY, GEMINI_*_MODEL |

### Backend (참조 — 패턴 학습 + Tool 호출 대상)
| 파일 | 참조 이유 |
|------|----------|
| `backend/api/routers/auth.py` | POST 라우터 패턴 (최신) |
| `backend/api/services/auth_service.py` | 서비스 패턴 (최신) |
| `backend/api/repositories/price_repo.py` | 가격 DB 조회 (Tool에서 호출) |
| `backend/api/repositories/factor_repo.py` | 팩터 DB 조회 (Tool에서 호출) |
| `backend/api/repositories/signal_repo.py` | 시그널 DB 조회 (Tool에서 호출) |
| `backend/api/repositories/backtest_repo.py` | 백테스트 DB 조회 (Tool에서 호출) |
| `backend/api/services/correlation_service.py` | 상관행렬 계산 (Tool에서 호출) |
| `backend/api/dependencies.py` | get_current_user DI (chat 인증) |
| `.claude/skills/langgraph-dev/SKILL.md` | LangGraph 구현 가이드 |

### Frontend (수정 대상)
| 파일 | 수정 내용 |
|------|----------|
| `frontend/src/components/layout/Layout.tsx` | ChatPanel 통합 (토글 버튼) |

### Frontend (신규)
| 파일 | 용도 |
|------|------|
| `frontend/src/types/chat.ts` | ChatSession, ChatMessage, SSE 이벤트 타입 |
| `frontend/src/api/chat.ts` | createSession, getSession, sendMessage API |
| `frontend/src/hooks/useSSE.ts` | fetch + ReadableStream SSE 파싱 (POST 지원) |
| `frontend/src/store/chatStore.ts` | Zustand: sessions, messages, streaming state |
| `frontend/src/components/chat/ChatPanel.tsx` | 우측 슬라이드 채팅 패널 |
| `frontend/src/components/chat/MessageBubble.tsx` | 메시지 버블 (user/assistant/tool) |
| `frontend/src/components/chat/ChatInput.tsx` | 메시지 입력 + 전송 |

## 2. 데이터 인터페이스

### 입력 (어디서 읽는가)
| 소스 | 데이터 | 용도 |
|------|--------|------|
| POST body | user_message (자연어) | 채팅 질의 |
| Authorization 헤더 | Bearer token | 사용자 식별 |
| DB `price_daily` | 가격 데이터 | Tool: get_prices |
| DB `factor_daily` | 팩터 데이터 | Tool: get_factors |
| DB `signal_daily` | 시그널 데이터 | Tool: get_signals |
| DB `backtest_run` | 백테스트 목록 | Tool: list_backtests |
| 상관행렬 서비스 | 상관계수 | Tool: get_correlation |

### 출력 (어디에 쓰는가)
| 대상 | 데이터 | 용도 |
|------|--------|------|
| DB `chat_sessions` | 세션 메타데이터 | 대화 이력 관리 |
| DB `chat_messages` | role, content, tool_payload | 대화 저장 |
| SSE Response | text_delta, tool_call, tool_result, done | 실시간 스트리밍 |

### DB 스키마 (신규 2 테이블)

```sql
-- chat_sessions
CREATE TABLE chat_sessions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       VARCHAR(200),
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT now()
);
CREATE INDEX ix_chat_sessions_user_id ON chat_sessions(user_id);

-- chat_messages
CREATE TABLE chat_messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL,  -- 'user', 'assistant', 'tool'
    content         TEXT,
    tool_payload    JSONB,  -- tool_calls / tool_results
    token_count     INTEGER,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT now()
);
CREATE INDEX ix_chat_messages_session_id ON chat_messages(session_id);
```

### API 엔드포인트 (신규 3개)

| Method | Path | Auth | 설명 |
|--------|------|------|------|
| POST | `/v1/chat/sessions` | Required | 채팅 세션 생성 → SessionResponse |
| GET | `/v1/chat/sessions/{session_id}` | Required | 세션 + 메시지 조회 |
| POST | `/v1/chat/sessions/{session_id}/messages` | Required | 메시지 전송 → SSE 스트리밍 |

### SSE 이벤트 포맷

```
data: {"type": "text_delta", "content": "삼성전자의 "}
data: {"type": "text_delta", "content": "현재 가격은..."}
data: {"type": "tool_call", "name": "get_prices", "args": {"asset_id": "005930", "days": 30}}
data: {"type": "tool_result", "name": "get_prices", "data": {...}}
data: {"type": "done"}
```

### LangGraph 구조

```
START → agent (Gemini Pro + tool binding)
              ↓ (tool_calls 있으면)
         tools (ToolNode: get_prices, get_factors, ...)
              ↓
         agent (Tool 결과 기반 응답 생성)
              ↓ (tool_calls 없으면)
         END
```

## 3. 주요 결정사항

| 결정 | 선택 | 대안 | 근거 |
|------|------|------|------|
| LLM 프레임워크 | LangGraph | 직접 구현, LangChain Agent | 명시적 그래프, SSE 이벤트 분리, checkpointer 내장 |
| LLM 모델 | Gemini 3.1 Pro | Claude, GPT-4 | 비용 효율 (무료 티어), Tool 호출 지원 |
| 스트리밍 | SSE (StreamingResponse) | WebSocket | HTTP 호환, 구현 간편, 단방향 충분 |
| SSE 클라이언트 | fetch + ReadableStream | EventSource | POST 지원 필요 (EventSource는 GET만) |
| Checkpointer | MemorySaver (dev) | PostgresSaver | Phase E에서 PostgresSaver 전환 |
| Chat UI | 우측 슬라이드 패널 | 별도 페이지 | 기존 대시보드와 동시 사용 |
| Tool DB 접근 | 별도 세션 생성 | DI 세션 공유 | Tool은 DI 컨텍스트 밖, 별도 세션 필요 |
| 메시지 저장 | user/assistant 모두 DB | assistant만 | 대화 이력 복원에 필요 |
| token_count | chat_messages 컬럼 | 별도 테이블 | 비용 추적 기반 (향후 제한 설정) |

## 4. 컨벤션 체크리스트

### 기존 컨벤션 (Phase B에서도 준수)
- [x] Router → Service → Repository 3계층 구조
- [x] Pydantic v2 스키마 (`ConfigDict(from_attributes=True)`)
- [x] Repository: 함수형 모듈
- [x] DI: `Depends(get_db)`, `Depends(get_current_user)`
- [x] `Mapped[]` + `mapped_column()` (SQLAlchemy 2.0)
- [x] 인코딩: utf-8 explicit
- [x] 환경변수 하드코딩 금지

### Phase B 신규 컨벤션
- [ ] SSE 이벤트: `data: {json}\n\n` 포맷 (text_delta, tool_call, tool_result, done)
- [ ] LangGraph Tool: DB 조회만 수행, LLM 직접 호출 금지
- [ ] Tool 반환값: 문자열 (JSON serialize)
- [ ] Tool 내 DB 세션: `with SessionLocal() as db:` 패턴
- [ ] chat 엔드포인트: 인증 필수 (`get_current_user`)
- [ ] 세션 소유권: `user_id` 검증 (다른 사용자 세션 접근 금지)
- [ ] 시스템 프롬프트: 한국어 분석 도우미, 데이터 근거 기반 응답 강제
- [ ] Zustand chatStore: authStore와 분리

### 파일 명명 규칙
| 유형 | 위치 | 파일명 |
|------|------|--------|
| 모델 | `db/models.py` | 기존 파일에 추가 |
| LLM Graph | `api/services/llm/graph.py` | 신규 |
| LLM Tools | `api/services/llm/tools.py` | 신규 |
| LLM Prompts | `api/services/llm/prompts.py` | 신규 |
| 스키마 | `api/schemas/chat.py` | 신규 |
| Repository | `api/repositories/chat_repo.py` | 신규 |
| Service | `api/services/chat/chat_service.py` | 신규 |
| Router | `api/routers/chat.py` | 신규 |
| Migration | `db/alembic/versions/xxx_add_chat_tables.py` | 자동 생성 |
