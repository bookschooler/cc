import os
import anthropic
from dotenv import load_dotenv

# __file__ 기준으로 위로 올라가며 .env 탐색
def _load_env():
    here = os.path.abspath(__file__)          # .../cc/agents/base.py
    path = os.path.dirname(here)              # .../cc/agents
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
        model="claude-haiku-4-5-20251001",  # 토큰 절약: haiku 사용
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text
