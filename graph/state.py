from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    topic: str

    # PM Agent
    plan: Optional[str]                   # 마크다운 계획서
    plan_version: int                     # 재계획 횟수 (max 3)
    human_plan_approved: Optional[bool]   # None=미결, True=승인, False=거절
    human_plan_feedback: Optional[str]    # 거절 시 피드백

    # Searcher (2단계: plan → exec)
    searcher_mini_plan: Optional[str]     # 어떤 데이터를 어디서 가져올지
    searcher_plan_approved: Optional[bool]
    searcher_plan_feedback: Optional[str]
    search_results: list                  # [{ticker, data, source_name, source_url, retrieved_at}]

    # 공통
    errors: list
    is_complete: bool
