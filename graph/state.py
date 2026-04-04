from typing import Optional
from typing_extensions import TypedDict


class AgentState(TypedDict):
    topic: str

    # ── Planner (OKRs + MECE Plan) ───────────────────────────────────────────
    objective: Optional[str]            # OKR: 달성 목표 한 문장
    key_results: list                   # OKR: 성공 기준 3개 (수치 포함)
    plan: Optional[str]                 # MECE 분석 계획 (마크다운)
    plan_explanation: Optional[str]     # Sophie 친화적 설명
    plan_version: int                   # 재계획 횟수

    # Planner peer review
    plan_peer_reviews: list             # [{agent, vote, feedback}, ...]
    plan_peer_passed: Optional[bool]    # 4명 중 3명 이상 PASS 여부
    plan_sophie_approved: Optional[bool]
    plan_sophie_feedback: Optional[str]

    # ── Researcher (Design Sprint + Methodology) ──────────────────────────────
    hypothesis: Optional[str]           # 핵심 가설 1개 (Design Sprint)
    poc_result: Optional[str]           # PoC 빠른 검증 결과
    methodology: Optional[str]          # 분석 방법론 (통계/ML 근거 포함)
    methodology_explanation: Optional[str]
    methodology_version: int

    # Researcher peer review
    methodology_peer_reviews: list
    methodology_peer_passed: Optional[bool]
    methodology_sophie_approved: Optional[bool]
    methodology_sophie_feedback: Optional[str]

    # ── Analyst ↔ Reviewer (Launch and Iterate) ───────────────────────────────
    code: Optional[str]                 # 현재 Python 코드
    analysis_results: Optional[str]     # 코드 실행 결과 (stdout)
    code_error: Optional[str]           # 실행 오류 (stderr)
    analysis_explanation: Optional[str]
    analysis_iteration: int             # Analyst 반복 횟수 (skeleton→완성)

    # Reviewer (코드·통계 QA)
    review_passed: Optional[bool]
    review_feedback: Optional[str]
    review_iteration: int               # 최대 3회

    # Analysis peer review (reviewer pass 후)
    analysis_peer_reviews: list
    analysis_peer_passed: Optional[bool]
    analysis_sophie_approved: Optional[bool]
    analysis_sophie_feedback: Optional[str]

    # ── Reporter (PPT + MD + Blameless Post-mortem) ───────────────────────────
    final_report_md: Optional[str]
    final_report_ppt_path: Optional[str]
    postmortem: Optional[str]           # 에이전트 개선 제안서
    report_explanation: Optional[str]

    # Report peer review
    report_peer_reviews: list
    report_peer_passed: Optional[bool]
    report_sophie_approved: Optional[bool]
    report_sophie_feedback: Optional[str]

    # ── Common ────────────────────────────────────────────────────────────────
    errors: list
    is_complete: bool
