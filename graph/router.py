from graph.state import AgentState


def route_after_plan_review(state: AgentState) -> str:
    """PM 계획 승인 여부에 따라 라우팅."""
    if state.get("human_plan_approved") is True:
        return "searcher_plan"
    return "pm"  # 거절 → PM 재계획


def route_after_searcher_exec(state: AgentState) -> str:
    """Searcher 미니플랜 승인 여부에 따라 라우팅.
    interrupt_before=["searcher_exec"] 이후 재개 시 호출됨.
    """
    if state.get("searcher_plan_approved") is True:
        return "searcher_run"   # 승인 → 실제 검색 실행
    return "searcher_plan"      # 거절 → 미니플랜 재작성
