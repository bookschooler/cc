import os
import anthropic
from dotenv import load_dotenv

# __file__ 기준으로 위로 올라가며 .env 탐색
def _load_env():
    here = os.path.abspath(__file__)
    path = os.path.dirname(here)
    for _ in range(10):
        candidate = os.path.join(path, ".env")
        if os.path.isfile(candidate):
            load_dotenv(candidate, override=True)
            return
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent

_load_env()

_client = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다. .env 파일을 확인하세요.")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def call_claude(system: str, user: str, max_tokens: int = 1024) -> str:
    """Claude API 호출 (토큰 절약: 기본 max_tokens=1024)."""
    client = get_client()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text


# ── Self-Review 공통 헬퍼 ──────────────────────────────────────────────────────
_SELF_REVIEW_SYSTEM = """You are {agent_name}. Critically review your own output against the checklist below.
Be honest — the goal is to catch problems BEFORE your teammates see it.

Checklist:
{checklist}

Respond ONLY in this exact format:

SELF_REVIEW: PASS
ISSUES: None

or

SELF_REVIEW: FAIL
ISSUES:
- [specific issue 1]
- [specific issue 2]"""


def self_review(output: str, checklist: list[str], agent_name: str) -> tuple[bool, list[str]]:
    """에이전트가 자신의 출력물을 체크리스트 기반으로 자기 검토.

    Args:
        output: 검토할 출력물 (앞 2000자만 사용)
        checklist: 체크리스트 항목 목록
        agent_name: 에이전트 이름 (프롬프트에 사용)

    Returns:
        (passed: bool, issues: list[str])
    """
    checklist_text = "\n".join(f"- {item}" for item in checklist)
    system = _SELF_REVIEW_SYSTEM.format(
        agent_name=agent_name,
        checklist=checklist_text,
    )
    result = call_claude(system, f"내 출력물:\n{output[:2000]}", max_tokens=400)

    passed = "SELF_REVIEW: PASS" in result
    issues = []
    if not passed:
        capture = False
        for line in result.splitlines():
            if line.strip().startswith("ISSUES:"):
                capture = True
                continue
            if capture and line.strip().startswith("- "):
                issues.append(line.strip()[2:])
    return passed, issues
