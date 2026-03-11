---
name: langgraph-dev
description: LangGraph + Gemini 기반 AI 에이전트 개발 가이드. StateGraph, Tool 정의, SSE 스트리밍, Checkpointer.
---

# LangGraph Development Guidelines

## When to Use

- LangGraph 그래프/노드/엣지 구현
- LangChain Tool 정의 (DB 조회, 분석 호출)
- SSE 스트리밍 (astream_events → FastAPI)
- Checkpointer 설정 (메모리 → PostgresStore)
- 시스템 프롬프트 관리

---

## Package Stack

```
langgraph                # 그래프 엔진
langchain-core           # Tool, PromptTemplate, Message 타입
langchain-google-genai   # ChatGoogleGenerativeAI
```

## Model Routing

| 모델 | 용도 |
|------|------|
| `gemini-3.1-pro-preview` | 메인 챗봇, 분석 해석, 도구 호출 |
| `gemini-3.1-flash-lite-preview` | 요청 분류, 온보딩, 단순 응답 |

## Directory Structure

```
api/services/llm/
  graph.py       # StateGraph 정의 (agent→tools 루프)
  tools.py       # @tool 함수 (prices, factors, correlation 등)
  prompts.py     # ChatPromptTemplate 시스템 프롬프트
```

---

## Core Patterns

### 1. 모델 초기화

```python
from langchain_google_genai import ChatGoogleGenerativeAI

pro = ChatGoogleGenerativeAI(model="gemini-3.1-pro-preview", google_api_key=settings.google_api_key)
lite = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite-preview", google_api_key=settings.google_api_key)
```

### 2. Graph 구조 (agent → tools 루프)

```python
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode

graph = StateGraph(MessagesState)
graph.add_node("agent", agent_node)       # pro 모델 + tool binding
graph.add_node("tools", ToolNode(tools))
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", route_tools)
graph.add_edge("tools", "agent")
app = graph.compile(checkpointer=checkpointer)
```

### 3. 조건 엣지

```python
def route_tools(state: MessagesState):
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END
```

### 4. Tool 정의

```python
from langchain_core.tools import tool

@tool
def get_prices(asset_id: str, days: int) -> str:
    """자산의 최근 N일 가격 데이터 조회"""
    # DB 조회 → JSON 문자열 반환
```

### 5. SSE 스트리밍 (FastAPI)

```python
async def event_generator():
    async for event in app.astream_events(
        {"messages": [HumanMessage(content=question)]},
        config={"configurable": {"thread_id": session_id}},
        version="v2",
    ):
        if event["event"] == "on_chat_model_stream":
            yield f"data: {json.dumps({'type': 'text_delta', 'content': chunk})}\n\n"
        elif event["event"] == "on_tool_end":
            yield f"data: {json.dumps({'type': 'tool_result', 'data': event['data']})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"

return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### 6. Checkpointer

```python
# Dev
from langgraph.checkpoint.memory import MemorySaver

# Production (Phase E)
from langgraph.checkpoint.postgres import PostgresSaver
```

---

## Anti-Patterns

| Pattern | Problem |
|---------|---------|
| Tool에서 LLM 직접 호출 | 무한 재귀 위험. Tool은 데이터만 반환 |
| 그래프 밖에서 상태 직접 변경 | checkpointer 무효화 |
| EventSource (GET) 사용 | POST 미지원. fetch + ReadableStream 사용 |

---

**Skill Status**: Initial guide. Phase B 구현 시 확장 예정.
