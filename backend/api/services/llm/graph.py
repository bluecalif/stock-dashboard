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
    )


async def agent_node(state: MessagesState, config: dict | None = None) -> dict:
    """LLM 호출 (tool binding 포함). 첫 호출 시 시스템 프롬프트 주입."""
    deep_mode = (config or {}).get("configurable", {}).get("deep_mode", False)
    model = _build_model(deep_mode).bind_tools(all_tools)
    messages = state["messages"]
    # 시스템 프롬프트가 없으면 맨 앞에 추가
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
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
