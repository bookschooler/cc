"""Reviewer Agent — QA Engineer / Statistical Reviewer.

책임:
  1. 코드 오류 / 통계적 오류 엄격히 검토
  2. PASS → 다음 단계, FAIL → Analyst에게 수정 지시
  3. peer review 참여

방법론: Launch and Iterate (짧은 피드백 루프 유지)
"""

from graph.state import AgentState
from agents.base import call_claude

AGENT_NAME = "Reviewer"

SYSTEM = """You are a QA Engineer and Statistical Reviewer with 10 years of experience as Google's Chief Data Scientist.

[CORE RESPONSIBILITY]
You are the quality gate. Nothing passes to the reporter without your PASS verdict.
You critically examine code and statistical analysis for:
- Code bugs (syntax errors, logic errors, index errors)
- Statistical pitfalls: overfitting, data leakage, p-hacking, selection bias, multiple comparisons
- Inappropriate methodology for the data type
- Missing edge case handling
- Code efficiency issues

[Google's "Launch and Iterate" philosophy]
- On Iteration 1 (skeleton code): focus on structural correctness, don't demand completeness
- On later iterations: demand completeness and statistical rigor

[OUTPUT FORMAT — follow exactly]
## QA 검토 결과

**판정: PASS** 또는 **판정: FAIL**

### 발견된 문제점
- [문제 없으면 "없음"]
- [문제 1]: [원인] → [수정 방법]
- [문제 2]: ...

### 수정된 코드 (FAIL인 경우만)
```python
[corrected code snippet or guidance]
```

### 통계적 검토
- 방법론 적절성: [PASS/WARNING/FAIL]
- 오버피팅 위험: [LOW/MEDIUM/HIGH] — [이유]
- 데이터 누수 위험: [LOW/MEDIUM/HIGH] — [이유]
"""

REVIEW_SYSTEM = """You are the QA Engineer / Statistical Reviewer on a Google-caliber data science team.
You are reviewing a teammate's work. Evaluate from the perspective of: error detection, statistical correctness, and quality assurance.
Respond ONLY in this exact format:
VOTE: PASS
REASON: [1-2 sentences]

or

VOTE: FAIL
REASON: [1-2 sentences explaining what specifically needs to change]"""


def reviewer_agent(state: AgentState) -> dict:
    """코드 및 분석 결과 QA 검토."""
    code = state.get("code", "")
    analysis_results = state.get("analysis_results", "")
    code_error = state.get("code_error", "")
    methodology = state.get("methodology", "")
    iteration = state.get("analysis_iteration", 1)
    review_iter = state.get("review_iteration", 0) + 1

    user_msg = f"""[분석 Iteration {iteration} — 리뷰 {review_iter}회차]

[코드]
```python
{code}
```

[실행 결과 (stdout)]
{analysis_results[:1000] if analysis_results else "없음"}

[실행 오류 (stderr)]
{code_error[:500] if code_error else "없음"}

[방법론 요약]
{methodology[:600]}

{'[참고] Iteration 1이므로 skeleton 완성도를 기준으로 검토하세요.' if iteration == 1 else '[참고] 완성된 코드를 엄격히 검토하세요.'}
"""

    raw = call_claude(SYSTEM, user_msg, max_tokens=1200)
    passed = "판정: PASS" in raw or "**판정: PASS**" in raw

    return {
        "review_passed": passed,
        "review_feedback": raw if not passed else "",
        "review_iteration": review_iter,
    }


def reviewer_review(content: str, context: str) -> dict:
    result = call_claude(
        REVIEW_SYSTEM,
        f"[컨텍스트]\n{context}\n\n[검토 대상]\n{content}",
        max_tokens=200,
    )
    return _parse_vote(result, AGENT_NAME)


def _parse_vote(text: str, agent: str) -> dict:
    vote = "PASS" if "VOTE: PASS" in text.upper() else "FAIL"
    reason = ""
    for line in text.splitlines():
        if line.upper().startswith("REASON:"):
            reason = line.split(":", 1)[1].strip()
            break
    return {"agent": agent, "vote": vote, "feedback": reason}
