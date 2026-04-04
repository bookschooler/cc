"""Planner Agent — Lead Data Analyst.

책임:
  1. OKR 정의 (Objective + Key Results 3개)
  2. OKR 기반 MECE 분석 계획 수립
  3. Self-review (자기 검토)
  4. Sophie 친화적 설명 생성

방법론: OKRs (Objectives and Key Results)
"""

from graph.state import AgentState
from agents.base import call_claude, self_review

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
- 약어/전문용어는 반드시 Full name 먼저: 예) OKR (Objectives and Key Results: 목표와 핵심 결과), MECE (Mutually Exclusive Collectively Exhaustive: 상호 배타적이고 전체를 포괄하는 원칙)
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

_SELF_CHECKLIST = [
    "OKR Objective가 비즈니스 목표와 직결되는 단 하나의 명확한 문장인가?",
    "Key Results 3개 모두 측정 가능한 수치(숫자)를 포함하는가?",
    "MECE 원칙이 지켜졌는가? (분석 단계들이 서로 겹치지 않고 전체를 커버하는가?)",
    "각 분석 단계에 목표/필요 데이터/예상 결과가 명시되어 있는가?",
    "Sophie 섹션에 전문용어 Full name 풀이가 포함되어 있는가?",
]


def planner_agent(state: AgentState) -> dict:
    """OKR 정의 + MECE 분석 계획 수립 (with self-review)."""
    topic = state["topic"]
    version = state.get("plan_version", 0)

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

    # ── 1차 생성 ──────────────────────────────────────────────────────────────
    raw = call_claude(SYSTEM, user_msg, max_tokens=1200)

    # ── Self-Review ───────────────────────────────────────────────────────────
    passed, issues = self_review(raw, _SELF_CHECKLIST, AGENT_NAME)
    if not passed and issues:
        print(f"  🔄 [Planner Self-Review] 문제 발견, 수정 중...")
        revision_msg = user_msg + "\n\n[자기 검토 결과 — 아래 문제를 반드시 수정]\n"
        revision_msg += "\n".join(f"- {i}" for i in issues)
        raw = call_claude(SYSTEM, revision_msg, max_tokens=1200)

    objective, key_results = _parse_okr(raw)

    return {
        "plan": raw,
        "objective": objective,
        "key_results": key_results,
        "plan_explanation": _extract_sophie_section(raw),
        "plan_version": version + 1,
        "plan_peer_reviews": [],
        "plan_peer_passed": None,
        "plan_sophie_approved": None,
        "plan_sophie_feedback": None,
    }


def planner_review(content: str, context: str) -> dict:
    result = call_claude(
        REVIEW_SYSTEM,
        f"[검토 컨텍스트]\n{context}\n\n[검토 대상]\n{content}",
        max_tokens=200,
    )
    return _parse_vote(result, AGENT_NAME)


def _parse_okr(text: str) -> tuple[str, list[str]]:
    objective = ""
    key_results = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("**Objective:**"):
            objective = s.replace("**Objective:**", "").strip()
        elif s.startswith("- KR"):
            key_results.append(s.lstrip("- ").strip())
    return objective, key_results[:3]


def _extract_sophie_section(text: str) -> str:
    marker = "## 📚 Sophie에게"
    idx = text.find(marker)
    return text[idx:].strip() if idx != -1 else text[-400:]


def _parse_vote(text: str, agent: str) -> dict:
    vote = "PASS" if "VOTE: PASS" in text.upper() else "FAIL"
    reason = ""
    for line in text.splitlines():
        if line.upper().startswith("REASON:"):
            reason = line.split(":", 1)[1].strip()
            break
    return {"agent": agent, "vote": vote, "feedback": reason}
