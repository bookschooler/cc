from graph.state import AgentState
from agents.base import call_claude
from tools.search_tools import get_multiple_stocks, extract_tickers_from_plan, firecrawl_search

PLAN_SYSTEM = """당신은 데이터 검색 에이전트입니다.
분석 계획을 보고 어떤 데이터를 어디서 가져올지 간결한 검색 계획을 작성하세요.

형식:
검색할 데이터:
1. [데이터명] - ticker: [코드] / 출처: Yahoo Finance
2. [뉴스/기사] - 키워드: [검색어] / 출처: Firecrawl 웹검색
...

예상 소요: ~N초"""


def searcher_plan_agent(state: AgentState) -> dict:
    """Searcher 미니플랜 작성 (실행 전 승인받을 계획)."""
    plan = state.get("plan", "")
    feedback = state.get("searcher_plan_feedback", "")

    user_msg = f"분석 계획:\n{plan}"
    if feedback:
        user_msg += f"\n\n피드백: {feedback}\n위 피드백을 반영해 검색 계획을 수정하세요."

    mini_plan = call_claude(PLAN_SYSTEM, user_msg, max_tokens=300)

    return {
        "searcher_mini_plan": mini_plan,
        "searcher_plan_approved": None,   # 승인 초기화
        "searcher_plan_feedback": None,
    }


def searcher_exec_agent(state: AgentState) -> dict:
    """실제 데이터 수집 (승인 후 실행)."""
    plan = state.get("plan", "")
    mini_plan = state.get("searcher_mini_plan", "")

    # 계획 텍스트에서 ticker 추출
    combined = plan + "\n" + mini_plan
    tickers = extract_tickers_from_plan(combined)

    # ticker가 없으면 기본 ticker 사용
    if not tickers:
        tickers = ["SPY"]  # S&P500 ETF 기본값

    # 중복 제거, 최대 5개
    tickers = list(dict.fromkeys(tickers))[:5]

    print(f"  📡 수집 중: {', '.join(tickers)}")
    results = get_multiple_stocks(tickers)

    # 계획에 뉴스/기사/최신동향 키워드가 있으면 firecrawl 검색 추가
    news_keywords = ["뉴스", "기사", "최신", "동향", "전망", "분석", "news", "trend", "outlook"]
    if any(kw in combined.lower() for kw in news_keywords):
        # 분석 주제를 검색 쿼리로 사용
        topic = state.get("topic", plan[:50])
        print(f"  🌐 웹 검색 중: {topic}")
        web_results = firecrawl_search(topic, limit=3)
        results = results + web_results

    return {"search_results": results}
