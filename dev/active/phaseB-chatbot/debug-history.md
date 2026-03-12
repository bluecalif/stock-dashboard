# Phase B: Chatbot Debug History
> Last Updated: 2026-03-12

## Bug Table

| # | Module | Issue | Fix | Commit |
|---|--------|-------|-----|--------|
| 1 | graph.py | Gemini 429 쿼타 초과 | OpenAI GPT-5로 전환 | `807c33f` |
| 2 | graph.py | OpenAI Test2 키 크레딧 소진 | book-process 키로 교체 | (env only) |
| 3 | chat_service.py | ToolMessage JSON 직렬화 에러 (langchain-core 1.x) | `.content` 속성 추출 + `str()` 래핑 | `689dedf` |
| 4 | ChatPanel.tsx | Vercel 빌드 실패 — unused `stopStream` (TS6133) | 변수 제거 | `2f21d0d` |

### B.18-1: Gemini → OpenAI 전환

**증상**: Gemini API 429 `Resource has been exhausted`
**원인**: 무료 티어 쿼타 초과 + Google Cloud 결제 설정 불가
**수정**:
1. `langchain-google-genai` → `langchain-openai` 패키지 교체
2. `ChatGoogleGenerativeAI` → `ChatOpenAI` 클래스 교체
3. settings: `google_api_key` → `openai_api_key`, `gemini_*` → `llm_*`
4. 패키지 업그레이드: langgraph 1.1.1, langchain-core 1.2.18

### B.18-2: ToolMessage 직렬화

**증상**: Tool 호출 성공 후 SSE에서 에러 이벤트 반환
**원인**: langchain-core 1.x에서 `on_tool_end` 이벤트의 `output`이 string → `ToolMessage` 객체로 변경
**수정**: `hasattr(raw_output, "content")` 체크 후 `.content` 속성 추출

### B.18-3: Vercel 빌드 실패

**증상**: 프로덕션에서 ChatPanel 💬 버튼 미표시
**원인**: `ChatPanel.tsx`에서 `stopStream` 선언만 하고 사용 안 함 → `tsc` TS6133 에러 → Vercel 빌드 실패
**수정**: unused 변수 제거

## Modified Files Summary

```
backend/
  config/settings.py              (수정: OpenAI 설정)
  api/services/llm/graph.py       (신규: StateGraph + deep_mode)
  api/services/llm/tools.py       (신규: 5개 Tool)
  api/services/llm/prompts.py     (신규: 시스템 프롬프트)
  api/schemas/chat.py             (신규: 스키마 + deep_mode)
  api/repositories/chat_repo.py   (신규: Repository)
  api/services/chat/chat_service.py (신규: SSE 오케스트레이션)
  api/routers/chat.py             (신규: 4 endpoints)
  api/main.py                     (수정: 라우터 등록)
  db/models.py                    (수정: ChatSession, ChatMessage)
  pyproject.toml                  (수정: langchain-openai)
  .env.example                    (수정: OpenAI 설정)

frontend/
  src/types/chat.ts               (신규)
  src/api/chat.ts                 (신규: deep_mode)
  src/hooks/useSSE.ts             (신규)
  src/store/chatStore.ts          (신규: deepMode)
  src/components/chat/ChatPanel.tsx    (신규)
  src/components/chat/MessageBubble.tsx (신규)
  src/components/chat/ChatInput.tsx    (신규: 심층모드 토글)
  src/components/layout/Layout.tsx     (수정: 💬 버튼)

.claude/skills/langgraph-dev/SKILL.md (수정: OpenAI 가이드)
```

## Lessons Learned

1. **LangChain 메이저 버전 업그레이드 시 반환 타입 확인** — langchain-core 0.3 → 1.x에서 `on_tool_end` output 타입 변경
2. **TypeScript strict mode에서 unused 변수** — `tsc -b` 빌드 시 사용하지 않는 destructured 변수도 에러
3. **LLM API 키 쿼타** — 무료 티어 한도 미리 확인, 결제 설정 필수
4. **GitHub Push Protection** — session-compact 등 문서에 API 키 포함 시 push 거부됨
