from graph.state import AgentState
from agents.base import call_claude

SYSTEM = """당신은 데이터 분석 PM 에이전트입니다.
사용자의 분석 주제를 받아 간결한 분석 계획을 작성하세요.
계획은 마크다운 형식으로, 다음 항목을 포함하세요:
1. 분석 목적 (1-2문장)
2. 필요한 데이터 소스 (금융 데이터 위주로 yfinance ticker 명시)
3. 분석 접근 방법 (2-3단계)
4. 예상 결과물

간결하게 작성하세요 (200자 이내)."""


def pm_agent(state: AgentState) -> dict:
    topic = state["topic"]
    feedback = state.get("human_plan_feedback", "")
    plan_version = state.get("plan_version", 0)

    user_msg = f"분석 주제: {topic}"
    if feedback:
        user_msg += f"\n\n이전 계획에 대한 피드백: {feedback}\n위 피드백을 반영해서 계획을 다시 작성해주세요."

    plan = call_claude(SYSTEM, user_msg, max_tokens=512)

    return {
        "plan": plan,
        "plan_version": plan_version + 1,
        "human_plan_approved": None,  # 승인 초기화
        "human_plan_feedback": None,
    }
