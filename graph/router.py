"""라우팅 로직.

각 단계별 조건부 엣지 함수 모음.
"""

from graph.state import AgentState

MAX_PLAN_VERSIONS       = 4
MAX_METHODOLOGY_VERSIONS = 4
MAX_REVIEW_ITERATIONS   = 3
MAX_REPORT_VERSIONS     = 3


# ── Plan 단계 ──────────────────────────────────────────────────────────────────
def route_after_peer_review_plan(state: AgentState) -> str:
    """plan peer review 결과에 따라 라우팅."""
    if state.get("plan_peer_passed"):
        return "sophie_plan"        # Sophie 투표로 이동
    if state.get("plan_version", 0) >= MAX_PLAN_VERSIONS:
        return "sophie_plan"        # 최대 반복 초과 → 강제 통과
    return "planner"                # 재작성


def route_after_sophie_plan(state: AgentState) -> str:
    """Sophie 투표 결과에 따라 라우팅."""
    if state.get("plan_sophie_approved") is True:
        return "researcher"
    if state.get("plan_version", 0) >= MAX_PLAN_VERSIONS:
        return "researcher"         # 최대 반복 초과 → 강제 진행
    return "planner"


# ── Methodology 단계 ──────────────────────────────────────────────────────────
def route_after_peer_review_methodology(state: AgentState) -> str:
    if state.get("methodology_peer_passed"):
        return "sophie_methodology"
    if state.get("methodology_version", 0) >= MAX_METHODOLOGY_VERSIONS:
        return "sophie_methodology"
    return "researcher"


def route_after_sophie_methodology(state: AgentState) -> str:
    if state.get("methodology_sophie_approved") is True:
        return "analyst"
    if state.get("methodology_version", 0) >= MAX_METHODOLOGY_VERSIONS:
        return "analyst"
    return "researcher"


# ── Analyst ↔ Reviewer 루프 (Launch and Iterate) ──────────────────────────────
def route_after_reviewer(state: AgentState) -> str:
    """Reviewer PASS/FAIL에 따라 라우팅."""
    if state.get("review_passed") is True:
        return "peer_review_analysis"
    if state.get("review_iteration", 0) >= MAX_REVIEW_ITERATIONS:
        return "peer_review_analysis"   # 최대 반복 초과 → 강제 통과
    return "analyst"                    # 코드 수정 요청


# ── Analysis 단계 ─────────────────────────────────────────────────────────────
def route_after_peer_review_analysis(state: AgentState) -> str:
    if state.get("analysis_peer_passed"):
        return "sophie_analysis"
    if state.get("analysis_iteration", 0) >= MAX_REVIEW_ITERATIONS:
        return "sophie_analysis"
    return "analyst"


def route_after_sophie_analysis(state: AgentState) -> str:
    if state.get("analysis_sophie_approved") is True:
        return "reporter"
    if state.get("analysis_iteration", 0) >= MAX_REVIEW_ITERATIONS:
        return "reporter"
    return "analyst"


# ── Report 단계 ───────────────────────────────────────────────────────────────
def route_after_peer_review_report(state: AgentState) -> str:
    if state.get("report_peer_passed"):
        return "sophie_report"
    if state.get("plan_version", 0) >= MAX_REPORT_VERSIONS:
        return "sophie_report"
    return "reporter"


def route_after_sophie_report(state: AgentState) -> str:
    if state.get("report_sophie_approved") is True:
        return "save_output"
    if state.get("plan_version", 0) >= MAX_REPORT_VERSIONS:
        return "save_output"
    return "reporter"
