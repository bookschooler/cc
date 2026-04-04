"""Planner Agent — Lead Data Analyst.

책임:
  1. OKR 정의 (Objective + Key Results 3개)
  2. OKR 기반 MECE 분석 계획 수립
  3. Sophie 친화적 설명 생성

방법론: OKRs (Objectives and Key Results)
"""

from graph.state import AgentState
from agents.base import call_claude

# ── 에이전트 정체성 ────────────────────────────────────────────────────────────
AGENT_NAME = "Planner"

SYSTEM = """You are a Lead Data Analyst with 10 years of experience as Google's Chief Data Scientist.

[CORE RESPONSIBILITY]
You set the strategic direction for data analysis projects. Before planning anything, you first define OKRs (Objectives and Key Results) — a goal-setting framework used throughout Google that clarifies WHAT to achieve and HOW to measure success.

[YOUR PROCESS]
1. Define ONE clear Objective: what business goal does this analysis serve?
2. Define 3 Key Results: specific, measurable success criteria (must include numbers)
3. Create a MECE (Mutually Exclusive, Collectively Exhaustive) analysis plan based on the OKRs
   - MECE means: steps don't overlap AND together they cover everything needed
4. Write a Sophie explanation (see below)

[OUTPUT FORMAT — follow exactly]
## OKR

**Objective:** [single sentence — the WHY of this project]

**Key Results:**
- KR1: [specific metric + target number]
- KR2: [specific metric + target number]
- KR3: [specific metric + target number]

## Analysis Plan

[MECE breakdown of analysis steps — numbered, each step has: goal / data needed / expected output]

## 📚 Sophie에게

[설명 규칙 엄수]
- 약어/전문용어는 반드시 Full name 먼저: 예) OKR (Objectives and Key Results: 목표와 핵심 결과)
- 지금 한 일 → 왜 했는지 → 전체에서 어떤 의미인지 순서로
- Sophie가 "왜?"라고 물을 것 같은 부분을 먼저 찾아 답해둘 것
- 숫자/결과는 비즈니스 언어로 번역
- 마지막에: 💡 오늘의 개념: [개념명 (Full name)] — [2~3문장 쉬운 설명]
"""

REVIEW_SYSTEM = """You are the Lead Data Analyst (Planner) on a Google-caliber data science team.
You are reviewing a teammate's work. Evaluate from the perspective of: strategic clarity, business alignment, and MECE structure.
Respond ONLY in this exact format:
VOTE: PASS
REASON: [1-2 sentences]

or

VOTE: FAIL
REASON: [1-2 sentences explaining what specifically needs to change]"""


# ── 메인 에이전트 함수 ─────────────────────────────────────────────────────────
def planner_agent(state: AgentState) -> dict:
    """OKR 정의 + MECE 분석 계획 수립."""
    topic = state["topic"]
    version = state.get("plan_version", 0)

    # 피드백 수집 (Sophie 또는 peer review)
    feedback_parts = []
    sophie_fb = state.get("plan_sophie_feedback")
    if sophie_fb:
        feedback_parts.append(f"Sophie 피드백: {sophie_fb}")

    peer_reviews = state.get("plan_peer_reviews", [])
    fail_reasons = [r["feedback"] for r in peer_reviews if r.get("vote") == "FAIL"]
    if fail_reasons:
        feedback_parts.append("팀 피드백:\n" + "\n".join(f"- {r}" for r in fail_reasons))

    user_msg = f"분석 주제: {topic}"
    if feedback_parts:
        user_msg += "\n\n[이전 계획에 대한 피드백 — 반드시 반영하세요]\n" + "\n\n".join(feedback_parts)

    raw = call_claude(SYSTEM, user_msg, max_tokens=1200)

    # OKR 파싱
    objective, key_results = _parse_okr(raw)

    return {
        "plan": raw,
        "objective": objective,
        "key_results": key_results,
        "plan_explanation": _extract_sophie_section(raw),
        "plan_version": version + 1,
        # 승인 상태 초기화
        "plan_peer_reviews": [],
        "plan_peer_passed": None,
        "plan_sophie_approved": None,
        "plan_sophie_feedback": None,
    }


# ── Peer Review 함수 ───────────────────────────────────────────────────────────
def planner_review(content: str, context: str) -> dict:
    """다른 에이전트의 결과물을 Planner 관점에서 검토."""
    result = call_claude(
        REVIEW_SYSTEM,
        f"[검토 컨텍스트]\n{context}\n\n[검토 대상]\n{content}",
        max_tokens=200,
    )
    return _parse_vote(result, AGENT_NAME)


# ── 헬퍼 ──────────────────────────────────────────────────────────────────────
def _parse_okr(text: str) -> tuple[str, list[str]]:
    """OKR 섹션에서 Objective와 KR 추출."""
    objective = ""
    key_results = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("**Objective:**"):
            objective = stripped.replace("**Objective:**", "").strip()
        elif stripped.startswith("- KR"):
            kr = stripped.lstrip("- ").strip()
            key_results.append(kr)
    return objective, key_results[:3]


def _extract_sophie_section(text: str) -> str:
    """## 📚 Sophie에게 섹션 추출."""
    marker = "## 📚 Sophie에게"
    idx = text.find(marker)
    if idx == -1:
        return text[-400:]  # fallback
    return text[idx:].strip()


def _parse_vote(text: str, agent: str) -> dict:
    """VOTE: PASS/FAIL 형식 파싱."""
    vote = "PASS" if "VOTE: PASS" in text.upper() else "FAIL"
    reason = ""
    for line in text.splitlines():
        if line.upper().startswith("REASON:"):
            reason = line.split(":", 1)[1].strip()
            break
    return {"agent": agent, "vote": vote, "feedback": reason}
