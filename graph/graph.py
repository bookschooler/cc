from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from graph.state import AgentState
from graph.router import route_after_plan_review, route_after_searcher_exec
from agents.pm import pm_agent
from agents.searcher import searcher_plan_agent, searcher_exec_agent


def _passthrough(state: AgentState) -> dict:
    """interrupt 전 passthrough 노드."""
    return {}


def _save_output(state: AgentState) -> dict:
    """결과를 JSON 파일로 저장."""
    import json, os
    from datetime import datetime

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(base_dir, "outputs")
    os.makedirs(out_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    topic_safe = state["topic"][:30].replace(" ", "_").replace("/", "_")
    path = os.path.join(out_dir, f"{topic_safe}_{timestamp}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "topic": state["topic"],
                "plan": state.get("plan"),
                "search_results": state.get("search_results", []),
                "saved_at": datetime.now().isoformat(),
            },
            f,
            ensure_ascii=False,
            indent=2,
            default=str,
        )

    print(f"\n✅ 결과 저장 완료: {path}")
    return {"is_complete": True}


def build_graph(db_path: str | None = None):
    """LangGraph StateGraph 빌드.

    플로우:
      pm → [interrupt] human_plan_review →(승인)→ searcher_plan
                                         →(거절)→ pm
      searcher_plan → [interrupt] searcher_exec →(승인)→ searcher_run
                                                →(거절)→ searcher_plan
      searcher_run → save_output → END
    """
    builder = StateGraph(AgentState)

    builder.add_node("pm", pm_agent)
    builder.add_node("human_plan_review", _passthrough)   # interrupt 발생 지점
    builder.add_node("searcher_plan", searcher_plan_agent)
    builder.add_node("searcher_exec", _passthrough)       # interrupt 발생 지점
    builder.add_node("searcher_run", searcher_exec_agent)
    builder.add_node("save_output", _save_output)

    builder.set_entry_point("pm")
    builder.add_edge("pm", "human_plan_review")

    builder.add_conditional_edges(
        "human_plan_review",
        route_after_plan_review,
        {"searcher_plan": "searcher_plan", "pm": "pm"},
    )

    builder.add_edge("searcher_plan", "searcher_exec")

    builder.add_conditional_edges(
        "searcher_exec",
        route_after_searcher_exec,
        {"searcher_run": "searcher_run", "searcher_plan": "searcher_plan"},
    )

    builder.add_edge("searcher_run", "save_output")
    builder.add_edge("save_output", END)

    if db_path is None:
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "checkpoints.db")
    checkpointer = SqliteSaver.from_conn_string(db_path)

    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_plan_review", "searcher_exec"],
    )
