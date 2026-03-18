"""LangGraph StateGraph: agent → tools → agent 루프."""

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from config.settings import settings

from .prompts import SYSTEM_PROMPT
from .tools import all_tools


def _build_model(deep_mode: bool = False) -> ChatOpenAI:
    model_name = settings.llm_pro_model if deep_mode else settings.llm_lite_model
    return ChatOpenAI(
        model=model_name,
        api_key=settings.openai_api_key,
        max_retries=3,
        request_timeout=30,
    )


# 메시지 트리밍 — MemorySaver 토큰 누적 방지
_MAX_MESSAGES = 20


def _trim_messages(messages: list) -> list:
    """최근 _MAX_MESSAGES개만 유지 (SystemMessage 항상 보존)."""
    if len(messages) <= _MAX_MESSAGES:
        return messages
    # SystemMessage가 첫 번째이면 보존
    if messages and isinstance(messages[0], SystemMessage):
        return [messages[0]] + messages[-(_MAX_MESSAGES - 1):]
    return messages[-_MAX_MESSAGES:]


def _build_system_prompt(page_context: dict | None = None) -> str:
    """시스템 프롬프트에 page_context 정보를 추가."""
    if not page_context:
        return SYSTEM_PROMPT

    page_id = page_context.get("page_id", "home")
    asset_ids = page_context.get("asset_ids", [])
    params = page_context.get("params", {})

    ctx_lines = [
        SYSTEM_PROMPT,
        "",
        f"[현재 페이지: {page_id}]",
    ]
    if asset_ids:
        ctx_lines.append(f"[선택된 자산: {', '.join(asset_ids)}]")
    if params:
        ctx_lines.append(f"[페이지 파라미터: {params}]")
    ctx_lines.append(
        "사용자가 보고 있는 페이지 맥락에 맞게 답변하세요. "
        "해당 페이지의 Tool을 적극 활용하세요."
    )
    return "\n".join(ctx_lines)


async def agent_node(state: MessagesState, config: dict | None = None) -> dict:
    """LLM 호출 (tool binding 포함). 첫 호출 시 시스템 프롬프트 주입."""
    configurable = (config or {}).get("configurable", {})
    deep_mode = configurable.get("deep_mode", False)
    page_context = configurable.get("page_context")

    model = _build_model(deep_mode).bind_tools(all_tools)
    messages = list(state["messages"])
    # 시스템 프롬프트가 없으면 맨 앞에 추가
    if not messages or not isinstance(messages[0], SystemMessage):
        prompt = _build_system_prompt(page_context)
        messages = [SystemMessage(content=prompt)] + messages
    # 토큰 누적 방지 트리밍
    messages = _trim_messages(messages)
    response = await model.ainvoke(messages)
    return {"messages": [response]}


def route_tools(state: MessagesState) -> str:
    """tool_calls가 있으면 tools 노드로, 없으면 END."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


def build_graph():
    """컴파일된 LangGraph 앱 반환."""
    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(all_tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", route_tools)
    graph.add_edge("tools", "agent")

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)
