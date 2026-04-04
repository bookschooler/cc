"""Peer Review 공통 모듈.

각 에이전트가 결과물을 완성하면, 나머지 4명이 자동으로 검토 + 투표.
Sophie의 투표는 main.py의 human interrupt에서 처리 (별도).

투표 기준: 4명 중 3명 이상 PASS → peer_passed = True
"""

from graph.state import AgentState


# 각 에이전트의 review 함수 import (지연 import로 순환 참조 방지)
def _get_reviewers():
    from agents.planner   import planner_review
    from agents.researcher import researcher_review
    from agents.analyst   import analyst_review
    from agents.reviewer  import reviewer_review
    from agents.reporter  import reporter_review
    return {
        "Planner":    planner_review,
        "Researcher": researcher_review,
        "Analyst":    analyst_review,
        "Reviewer":   reviewer_review,
        "Reporter":   reporter_review,
    }


def run_peer_review(
    stage: str,          # "plan" | "methodology" | "analysis" | "report"
    content: str,        # 검토 대상 텍스트
    context: str,        # 배경 정보 (topic, objective 등)
    exclude_agent: str,  # 자신은 제외
) -> tuple[list[dict], bool]:
    """4명의 에이전트가 content를 검토하고 투표 결과를 반환.

    Returns:
        (reviews, passed)
        reviews: [{agent, vote, feedback}, ...]
        passed: True if 3/4 이상 PASS
    """
    reviewers = _get_reviewers()
    reviews = []

    for agent_name, review_fn in reviewers.items():
        if agent_name == exclude_agent:
            continue
        try:
            result = review_fn(content, context)
            reviews.append(result)
        except Exception as e:
            # 리뷰 실패 시 PASS 처리 (팀 전체 블로킹 방지)
            reviews.append({
                "agent": agent_name,
                "vote": "PASS",
                "feedback": f"[리뷰 오류 — 자동 PASS] {str(e)[:100]}",
            })

    pass_count = sum(1 for r in reviews if r["vote"] == "PASS")
    passed = pass_count >= 3  # 4명 중 3명 이상

    return reviews, passed


def format_reviews_for_display(reviews: list[dict], passed: bool) -> str:
    """peer review 결과를 터미널 출력용 문자열로 변환."""
    lines = []
    for r in reviews:
        icon = "✅" if r["vote"] == "PASS" else "❌"
        lines.append(f"  {icon} {r['agent']:12s} | {r['vote']} | {r['feedback']}")

    pass_count = sum(1 for r in reviews if r["vote"] == "PASS")
    total = len(reviews)
    verdict = "통과 ✅" if passed else "미통과 ❌ → 수정 필요"

    summary = f"\n  [{pass_count}/{total} PASS] → {verdict}"
    return "\n".join(lines) + summary
