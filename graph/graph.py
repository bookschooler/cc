"""StateGraph 정의.

플로우:
  planner → peer_review_plan → sophie_plan(interrupt) → researcher
  → peer_review_methodology → sophie_methodology(interrupt) → analyst
  → reviewer → peer_review_analysis → sophie_analysis(interrupt)
  → reporter → peer_review_report → sophie_report(interrupt)
  → save_output → END
"""

import json
import os
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from graph.state import AgentState
from graph.router import (
    route_after_peer_review_plan,
    route_after_sophie_plan,
    route_after_peer_review_methodology,
    route_after_sophie_methodology,
    route_after_reviewer,
    route_after_peer_review_analysis,
    route_after_sophie_analysis,
    route_after_peer_review_report,
    route_after_sophie_report,
)
from agents.planner    import planner_agent
from agents.researcher import researcher_agent
from agents.analyst    import analyst_agent
from agents.reviewer   import reviewer_agent
from agents.reporter   import reporter_agent
from graph.peer_review import run_peer_review


# ── Peer Review 노드 팩토리 ────────────────────────────────────────────────────
def _make_peer_review_node(stage: str, content_key: str, exclude_agent: str,
                            passed_key: str, reviews_key: str, context_fn):
    """peer review 노드 함수 생성기."""
    def node(state: AgentState) -> dict:
        content = state.get(content_key, "") or ""
        context = context_fn(state)
        reviews, passed = run_peer_review(stage, content, context, exclude_agent)
        return {reviews_key: reviews, passed_key: passed}
    node.__name__ = f"peer_review_{stage}"
    return node


def _plan_context(state):
    return f"주제: {state.get('topic','')}\nObjective: {state.get('objective','')}"

def _methodology_context(state):
    return f"주제: {state.get('topic','')}\n계획: {(state.get('plan') or '')[:400]}"

def _analysis_context(state):
    return f"주제: {state.get('topic','')}\n방법론: {(state.get('methodology') or '')[:300]}"

def _report_context(state):
    return f"주제: {state.get('topic','')}\n결과: {(state.get('analysis_results') or '')[:400]}"


# ── Passthrough 노드 (interrupt 발생 지점) ─────────────────────────────────────
def _passthrough(state: AgentState) -> dict:
    return {}


# ── 결과 저장 노드 ─────────────────────────────────────────────────────────────
def _save_output(state: AgentState) -> dict:
    out_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs"
    )
    os.makedirs(out_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = (state.get("topic") or "analysis")[:20].replace(" ", "_")

    # 마크다운 보고서 저장
    md_path = os.path.join(out_dir, f"{timestamp}_{safe_topic}.md")
    report_md = state.get("final_report_md", "") or ""
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    # JSON 메타데이터 저장
    json_path = os.path.join(out_dir, f"{timestamp}_{safe_topic}_meta.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "topic": state.get("topic"),
            "objective": state.get("objective"),
            "key_results": state.get("key_results", []),
            "plan_version": state.get("plan_version"),
            "methodology_version": state.get("methodology_version"),
            "analysis_iteration": state.get("analysis_iteration"),
            "review_iteration": state.get("review_iteration"),
            "ppt_path": state.get("final_report_ppt_path"),
            "saved_at": datetime.now().isoformat(),
        }, f, ensure_ascii=False, indent=2)

    # Post-mortem 누적 저장
    _append_postmortem(state)

    print(f"\n📄 보고서 저장: {md_path}")
    print(f"📋 메타데이터: {json_path}")
    return {"is_complete": True}


def _append_postmortem(state: AgentState):
    """post-mortem을 memory/postmortem_log.md에 누적 저장."""
    mem_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memory"
    )
    os.makedirs(mem_dir, exist_ok=True)
    log_path = os.path.join(mem_dir, "postmortem_log.md")
    postmortem = state.get("postmortem", "") or ""
    if not postmortem:
        return
    entry = f"\n\n---\n## {datetime.now().strftime('%Y-%m-%d %H:%M')} | {state.get('topic','')}\n\n{postmortem}"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)


# ── 그래프 빌드 ────────────────────────────────────────────────────────────────
def build_graph(db_path: str | None = None):
    builder = StateGraph(AgentState)

    # 에이전트 노드
    builder.add_node("planner",    planner_agent)
    builder.add_node("researcher", researcher_agent)
    builder.add_node("analyst",    analyst_agent)
    builder.add_node("reviewer",   reviewer_agent)
    builder.add_node("reporter",   reporter_agent)

    # Peer review 노드
    builder.add_node("peer_review_plan",
        _make_peer_review_node("plan", "plan", "Planner",
                               "plan_peer_passed", "plan_peer_reviews", _plan_context))
    builder.add_node("peer_review_methodology",
        _make_peer_review_node("methodology", "methodology", "Researcher",
                               "methodology_peer_passed", "methodology_peer_reviews", _methodology_context))
    builder.add_node("peer_review_analysis",
        _make_peer_review_node("analysis", "code", "Analyst",
                               "analysis_peer_passed", "analysis_peer_reviews", _analysis_context))
    builder.add_node("peer_review_report",
        _make_peer_review_node("report", "final_report_md", "Reporter",
                               "report_peer_passed", "report_peer_reviews", _report_context))

    # Sophie interrupt 노드 (passthrough — interrupt_before 적용)
    builder.add_node("sophie_plan",        _passthrough)
    builder.add_node("sophie_methodology", _passthrough)
    builder.add_node("sophie_analysis",    _passthrough)
    builder.add_node("sophie_report",      _passthrough)

    # 저장 노드
    builder.add_node("save_output", _save_output)

    # ── 엣지 ──────────────────────────────────────────────────────────────────
    builder.set_entry_point("planner")
    builder.add_edge("planner", "peer_review_plan")

    builder.add_conditional_edges("peer_review_plan", route_after_peer_review_plan,
        {"sophie_plan": "sophie_plan", "planner": "planner"})

    builder.add_conditional_edges("sophie_plan", route_after_sophie_plan,
        {"researcher": "researcher", "planner": "planner"})

    builder.add_edge("researcher", "peer_review_methodology")

    builder.add_conditional_edges("peer_review_methodology", route_after_peer_review_methodology,
        {"sophie_methodology": "sophie_methodology", "researcher": "researcher"})

    builder.add_conditional_edges("sophie_methodology", route_after_sophie_methodology,
        {"analyst": "analyst", "researcher": "researcher"})

    builder.add_edge("analyst", "reviewer")

    builder.add_conditional_edges("reviewer", route_after_reviewer,
        {"peer_review_analysis": "peer_review_analysis", "analyst": "analyst"})

    builder.add_conditional_edges("peer_review_analysis", route_after_peer_review_analysis,
        {"sophie_analysis": "sophie_analysis", "analyst": "analyst"})

    builder.add_conditional_edges("sophie_analysis", route_after_sophie_analysis,
        {"reporter": "reporter", "analyst": "analyst"})

    builder.add_edge("reporter", "peer_review_report")

    builder.add_conditional_edges("peer_review_report", route_after_peer_review_report,
        {"sophie_report": "sophie_report", "reporter": "reporter"})

    builder.add_conditional_edges("sophie_report", route_after_sophie_report,
        {"save_output": "save_output", "reporter": "reporter"})

    builder.add_edge("save_output", END)

    # ── 체크포인터 ─────────────────────────────────────────────────────────────
    if db_path is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base, "checkpoints.db")

    checkpointer = SqliteSaver.from_conn_string(db_path)

    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["sophie_plan", "sophie_methodology", "sophie_analysis", "sophie_report"],
    )
