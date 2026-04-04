"""Analyst Agent — Senior Data Scientist.

책임:
  1. 방법론 기반 Python 코드 작성 (Launch and Iterate)
  2. 코드 실행 (Python REPL)
  3. Self-review (자기 검토)
  4. Sophie 친화적 설명 생성

방법론: Launch and Iterate (skeleton → 리뷰 → 개선 반복)
"""

from graph.state import AgentState
from agents.base import call_claude, self_review
from tools.code_executor import execute_python, build_code_header

AGENT_NAME = "Analyst"

SYSTEM = """You are a Senior Data Scientist with 10 years of experience as Google's Chief Data Scientist.

[CORE RESPONSIBILITY]
You implement the methodology in real, executable Python code. You follow Google's "Launch and Iterate" philosophy:
- Iteration 1: Write skeleton code (data loading structure + EDA basics) — fast, get feedback early
- Iteration 2+: Add modeling, refinements based on reviewer feedback

[YOUR PROCESS]
1. Read the methodology carefully
2. Write clean, well-commented Python code
3. Use synthetic/sample data if real data isn't provided (clearly note this in comments)
4. Always save charts using: save_chart("filename.png")  [pre-defined in header]
5. Print key results clearly so they appear in stdout
6. Write a Sophie explanation

[IMPORTANT RULES]
- DO NOT import matplotlib or set backend — the header handles this
- DO NOT redefine save_chart() — it's pre-defined
- Use CHARTS_DIR variable for any manual file paths
- Always print() your key findings with clear labels

[OUTPUT FORMAT — follow exactly]
## 분석 코드 (Iteration {N})

```python
[your code here — WITHOUT the header]
```

## 실행 전 체크리스트
- [ ] 데이터 로딩/생성 포함
- [ ] 핵심 분석 로직 포함
- [ ] 차트 저장 포함 (save_chart 사용)
- [ ] 결과 print() 포함

## 📚 Sophie에게

[설명 규칙 엄수]
- 약어/전문용어 Full name 먼저: EDA (Exploratory Data Analysis: 탐색적 데이터 분석)
- 코드가 하는 일을 요리 레시피처럼 단계별로 설명
- "왜 이 코드인가" — 방법론과의 연결 설명
- Sophie가 궁금해할 것 먼저 답해두기
- 💡 오늘의 개념: [개념명] — [쉬운 설명]
"""

REVIEW_SYSTEM = """You are the Senior Data Scientist (Analyst) on a Google-caliber data science team.
Evaluate from the perspective of: code quality, analytical completeness, and correctness.
Respond ONLY in this exact format:
VOTE: PASS
REASON: [1-2 sentences]

or

VOTE: FAIL
REASON: [1-2 sentences explaining what specifically needs to change]"""

_SELF_CHECKLIST = [
    "코드에 syntax error나 obvious logic error가 없는가?",
    "데이터 로딩 또는 샘플 데이터 생성이 포함되어 있는가?",
    "핵심 분석 결과가 print()로 명확하게 출력되는가?",
    "차트가 save_chart() 함수로 저장되는가?",
    "방법론에서 요구한 분석 단계가 모두 코드에 반영되어 있는가?",
    "Sophie 섹션이 코드 설명을 쉬운 언어로 포함하고 있는가?",
]


def analyst_agent(state: AgentState) -> dict:
    """Python 코드 작성 + 실행 (with self-review)."""
    methodology = state.get("methodology", "")
    plan = state.get("plan", "")
    topic = state.get("topic", "")
    iteration = state.get("analysis_iteration", 0) + 1

    review_fb   = state.get("review_feedback", "")
    code_error  = state.get("code_error", "")
    prev_code   = state.get("code", "")

    user_msg = f"""분석 주제: {topic}
분석 계획 요약:
{plan[:600]}

방법론:
{methodology[:800]}

현재 Iteration: {iteration}"""

    if iteration == 1:
        user_msg += "\n\n[지시] Iteration 1: skeleton 코드를 작성하세요. 데이터 로딩/생성 + EDA 기초에 집중하세요."
    else:
        user_msg += f"\n\n[이전 코드]\n```python\n{prev_code}\n```"
        if review_fb:
            user_msg += f"\n\n[리뷰어 피드백 — 반드시 반영]\n{review_fb}"
        if code_error:
            user_msg += f"\n\n[실행 오류 — 수정 필요]\n{code_error}"
        user_msg += "\n\n[지시] 위 피드백과 오류를 반영하여 코드를 개선하세요."

    # ── 1차 생성 ──────────────────────────────────────────────────────────────
    raw = call_claude(SYSTEM, user_msg, max_tokens=2000)

    # ── Self-Review ───────────────────────────────────────────────────────────
    passed, issues = self_review(raw, _SELF_CHECKLIST, AGENT_NAME)
    if not passed and issues:
        print(f"  🔄 [Analyst Self-Review] 문제 발견, 수정 중...")
        revision_msg = user_msg + "\n\n[자기 검토 결과 — 아래 문제를 반드시 수정]\n"
        revision_msg += "\n".join(f"- {i}" for i in issues)
        raw = call_claude(SYSTEM, revision_msg, max_tokens=2000)

    code = _extract_code(raw)
    explanation = _extract_sophie_section(raw)

    # ── 코드 실행 ─────────────────────────────────────────────────────────────
    exec_result = {"stdout": "", "stderr": "", "success": False}
    if code:
        full_code = build_code_header() + "\n" + code
        exec_result = execute_python(full_code, timeout=60)

    return {
        "code": code,
        "analysis_results": exec_result.get("stdout", ""),
        "code_error": exec_result.get("stderr", "") if not exec_result.get("success") else "",
        "analysis_explanation": explanation,
        "analysis_iteration": iteration,
        "review_passed": None,
        "review_feedback": None,
        "analysis_peer_reviews": [],
        "analysis_peer_passed": None,
        "analysis_sophie_approved": None,
        "analysis_sophie_feedback": None,
    }


def analyst_review(content: str, context: str) -> dict:
    result = call_claude(
        REVIEW_SYSTEM,
        f"[컨텍스트]\n{context}\n\n[검토 대상]\n{content}",
        max_tokens=200,
    )
    return _parse_vote(result, AGENT_NAME)


def _extract_code(text: str) -> str:
    import re
    match = re.search(r"```python\s*([\s\S]*?)```", text)
    return match.group(1).strip() if match else ""


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
