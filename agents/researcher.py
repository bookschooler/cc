"""Researcher Agent — Data Science Researcher.

책임:
  1. 핵심 가설 1개 정의 (Design Sprint)
  2. PoC (Proof of Concept) 빠른 기술 검증
  3. 통계/ML 방법론 설계 (ArXiv + docs 참조)
  4. Knowledge Base 자동 업데이트 (논문 + 방법론)
  5. Self-review (자기 검토)
  6. Sophie 친화적 설명 생성

방법론: Design Sprints (빠른 가설 → PoC → 방법론 확정)
"""

from graph.state import AgentState
from agents.base import call_claude, self_review
from tools.search_tools import firecrawl_search
from tools.arxiv_tools import search_arxiv, format_papers_for_prompt

AGENT_NAME = "Researcher"

SYSTEM = """You are a Data Science Researcher with 10 years of experience as Google's Chief Data Scientist.

[CORE RESPONSIBILITY]
You design the most rigorous, mathematically validated methodology for each analysis project.
You follow Google Ventures' Design Sprint philosophy: don't spend weeks researching — pick the ONE most critical hypothesis and validate it fast.

[YOUR PROCESS]
1. Define ONE hypothesis: the single most important assumption the analysis depends on
2. Design a quick PoC (Proof of Concept) — one statistical test or model run to validate the hypothesis
3. Based on the hypothesis and PoC result, select the full methodology with clear mathematical justification
4. Reference academic sources (ArXiv) or official documentation where applicable
5. Write a Sophie explanation

[OUTPUT FORMAT — follow exactly]
## Design Sprint: 핵심 가설

**가설:** [단 하나의 핵심 가설 — 데이터로 검증 가능한 형태로]
**PoC 검증 방법:** [가장 빠른 검증 방법 1가지]
**PoC 결과:** [VALID / INVALID / UNCERTAIN + 이유]

## 분석 방법론

**선택 방법론:** [통계 검정 / ML 모델명]
**선택 근거:** [수학적·통계적 이유 — 왜 이 방법이 이 데이터에 적합한가]
**통계적 가정:** [이 방법을 쓰기 위해 데이터가 만족해야 하는 조건들]
**검증 방법:** [분석 후 결과를 어떻게 통계적으로 검증할 것인가]
**참고 자료:** [논문명 또는 공식 문서 URL]

**상세 단계:**
1. [전처리 단계]
2. [EDA (Exploratory Data Analysis: 탐색적 데이터 분석) 단계]
3. [모델링/분석 단계]
4. [검증 단계]

## 📚 Sophie에게

[설명 규칙 엄수]
- 약어/전문용어 Full name 먼저: PoC (Proof of Concept: 개념 증명), EDA (Exploratory Data Analysis: 탐색적 데이터 분석)
- "왜 이 방법인가"를 Sophie 눈높이로 설명
- 수식 대신 일상 비유 사용
- Sophie가 궁금할 것을 먼저 답해두기
- 💡 오늘의 개념: [개념명 (Full name)] — [쉬운 설명]
"""

REVIEW_SYSTEM = """You are the Data Science Researcher on a Google-caliber data science team.
Evaluate from the perspective of: methodological rigor, statistical validity, and hypothesis clarity.
Respond ONLY in this exact format:
VOTE: PASS
REASON: [1-2 sentences]

or

VOTE: FAIL
REASON: [1-2 sentences explaining what specifically needs to change]"""

_SELF_CHECKLIST = [
    "가설이 데이터로 검증 가능한 구체적인 형태인가? (예: 'X와 Y는 상관관계가 있다'처럼 구체적)",
    "PoC 검증 방법이 가장 빠르고 명확한 방법 1가지인가?",
    "방법론 선택의 수학적·통계적 근거가 명시되어 있는가?",
    "통계적 가정(Assumptions)이 명시되어 있는가?",
    "검증 방법(Validation Methods)이 구체적으로 명시되어 있는가?",
    "참고 논문 또는 공식 문서가 인용되어 있는가?",
]


def researcher_agent(state: AgentState) -> dict:
    """핵심 가설 정의 + PoC + 방법론 설계 (with self-review + KB update)."""
    plan = state.get("plan", "")
    objective = state.get("objective", "")
    topic = state.get("topic", "")
    version = state.get("methodology_version", 0)

    feedback_parts = []
    sophie_fb = state.get("methodology_sophie_feedback")
    if sophie_fb:
        feedback_parts.append(f"Sophie 피드백: {sophie_fb}")
    peer_reviews = state.get("methodology_peer_reviews", [])
    fail_reasons = [r["feedback"] for r in peer_reviews if r.get("vote") == "FAIL"]
    if fail_reasons:
        feedback_parts.append("팀 피드백:\n" + "\n".join(f"- {r}" for r in fail_reasons))

    # ArXiv 검색
    papers = search_arxiv(f"data analysis methodology {topic}", max_results=3)
    paper_context = format_papers_for_prompt(papers)

    # 웹 검색
    web_results = firecrawl_search(topic, limit=2)
    web_context = "\n".join(
        f"- {r.get('title','')}: {r.get('content','')[:200]}"
        for r in web_results if "error" not in r
    )

    user_msg = f"""분석 주제: {topic}
Objective: {objective}
분석 계획:
{plan}

[참고 논문]
{paper_context}

[최신 동향]
{web_context}"""

    if feedback_parts:
        user_msg += "\n\n[피드백 — 반드시 반영]\n" + "\n\n".join(feedback_parts)

    # ── 1차 생성 ──────────────────────────────────────────────────────────────
    raw = call_claude(SYSTEM, user_msg, max_tokens=1500)

    # ── Self-Review ───────────────────────────────────────────────────────────
    passed, issues = self_review(raw, _SELF_CHECKLIST, AGENT_NAME)
    if not passed and issues:
        print(f"  🔄 [Researcher Self-Review] 문제 발견, 수정 중...")
        revision_msg = user_msg + "\n\n[자기 검토 결과 — 아래 문제를 반드시 수정]\n"
        revision_msg += "\n".join(f"- {i}" for i in issues)
        raw = call_claude(SYSTEM, revision_msg, max_tokens=1500)

    hypothesis, poc_result = _parse_hypothesis(raw)
    methodology_name = _extract_methodology_name(raw)

    # ── Knowledge Base 업데이트 ───────────────────────────────────────────────
    _update_knowledge_base(papers, raw, methodology_name, topic)

    return {
        "hypothesis": hypothesis,
        "poc_result": poc_result,
        "methodology": raw,
        "methodology_explanation": _extract_sophie_section(raw),
        "methodology_version": version + 1,
        "methodology_peer_reviews": [],
        "methodology_peer_passed": None,
        "methodology_sophie_approved": None,
        "methodology_sophie_feedback": None,
    }


def researcher_review(content: str, context: str) -> dict:
    result = call_claude(
        REVIEW_SYSTEM,
        f"[컨텍스트]\n{context}\n\n[검토 대상]\n{content}",
        max_tokens=200,
    )
    return _parse_vote(result, AGENT_NAME)


# ── Knowledge Base 업데이트 ────────────────────────────────────────────────────
def _update_knowledge_base(papers: list, methodology_text: str,
                            methodology_name: str, topic: str):
    """논문과 방법론을 KB에 저장."""
    try:
        from tools.knowledge_base import save_paper, save_methodology

        # 논문 저장
        method_tags = [_safe_tag(methodology_name)] if methodology_name else ["data_analysis"]
        for p in papers:
            if "error" not in p and p.get("title"):
                sophie_sum = _generate_paper_summary(p)
                save_paper(
                    title=p["title"],
                    summary=p.get("summary", ""),
                    url=p.get("source_url", ""),
                    methodology_tags=method_tags,
                    sophie_summary=sophie_sum,
                )

        # 방법론 저장
        if methodology_name:
            assumptions = _extract_section(methodology_text, "통계적 가정")
            validation  = _extract_section(methodology_text, "검증 방법")
            sophie_exp  = _extract_sophie_section(methodology_text)
            paper_titles = [p.get("title", "") for p in papers if "error" not in p]
            save_methodology(
                name=methodology_name,
                description=f"{topic} 분석에 사용된 방법론",
                when_to_use=f"{topic}와 유사한 분석 목적일 때",
                assumptions=assumptions or "_상세 내용은 방법론 문서 참조_",
                validation_methods=validation or "_상세 내용은 방법론 문서 참조_",
                recent_papers=paper_titles[:3],
                sophie_explanation=sophie_exp,
                tags=method_tags,
            )
        print(f"  📚 Knowledge Base 업데이트 완료")
    except Exception as e:
        print(f"  [KB 업데이트 오류] {e}")


def _generate_paper_summary(paper: dict) -> str:
    """논문 요약을 Sophie 눈높이로 변환."""
    try:
        return call_claude(
            "당신은 데이터 사이언스 논문을 비전공자에게 쉽게 설명하는 전문가입니다. 2~3문장으로 핵심만 설명하세요.",
            f"논문 제목: {paper.get('title','')}\n요약: {paper.get('summary','')[:500]}",
            max_tokens=150,
        )
    except Exception:
        return ""


def _extract_methodology_name(text: str) -> str:
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("**선택 방법론:**"):
            return s.replace("**선택 방법론:**", "").strip()
    return ""


def _extract_section(text: str, section_name: str) -> str:
    lines = text.splitlines()
    capturing, result = False, []
    for line in lines:
        if section_name in line and line.strip().startswith("**"):
            capturing = True
            after = line.split(":**", 1)[-1].strip()
            if after:
                result.append(after)
            continue
        if capturing and line.strip().startswith("**"):
            break
        if capturing:
            result.append(line)
    return "\n".join(result).strip()


def _parse_hypothesis(text: str) -> tuple[str, str]:
    hypothesis, poc = "", ""
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("**가설:**"):
            hypothesis = s.replace("**가설:**", "").strip()
        elif s.startswith("**PoC 결과:**"):
            poc = s.replace("**PoC 결과:**", "").strip()
    return hypothesis, poc


def _extract_sophie_section(text: str) -> str:
    marker = "## 📚 Sophie에게"
    idx = text.find(marker)
    return text[idx:].strip() if idx != -1 else text[-400:]


def _safe_tag(name: str) -> str:
    import re
    return re.sub(r'\s+', '_', name.lower().strip())[:30]


def _parse_vote(text: str, agent: str) -> dict:
    vote = "PASS" if "VOTE: PASS" in text.upper() else "FAIL"
    reason = ""
    for line in text.splitlines():
        if line.upper().startswith("REASON:"):
            reason = line.split(":", 1)[1].strip()
            break
    return {"agent": agent, "vote": vote, "feedback": reason}
