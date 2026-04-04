#!/usr/bin/env python3
"""데이터 분석 에이전트팀 CLI 진입점.

사용법:
  python main.py "분석 주제"
  python main.py "고객 이탈률 분석"

팀 구성:
  Planner (Lead Data Analyst)  → OKRs + MECE 계획
  Researcher (Data Scientist)  → Design Sprint + 방법론
  Analyst (Senior DS)          → 코드 작성 + 실행
  Reviewer (QA Engineer)       → 코드/통계 검토
  Reporter (Data Storyteller)  → PPT + 보고서 + Post-mortem

Peer Review: 각 단계 완료 후 4명 자동 투표 → Sophie 최종 투표
"""

import sys
import json
import os
import uuid
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.table import Table
from rich import box

load_dotenv()
console = Console()

# ── Sophie 점수 관련 ──────────────────────────────────────────────────────────
SCORES_PATH = os.path.join(os.path.dirname(__file__), "memory", "agent_scores.json")
AGENT_NAMES = ["Planner", "Researcher", "Analyst", "Reviewer", "Reporter"]


def _load_scores() -> dict:
    if os.path.exists(SCORES_PATH):
        with open(SCORES_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {name: [] for name in AGENT_NAMES}


def _save_scores(scores: dict):
    os.makedirs(os.path.dirname(SCORES_PATH), exist_ok=True)
    with open(SCORES_PATH, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)


def _avg(lst: list) -> float:
    return round(sum(lst) / len(lst), 2) if lst else 0.0


def _show_team_scores(scores: dict):
    """팀 점수 현황을 테이블로 출력."""
    table = Table(title="📊 Sophie의 팀 성과 평가", box=box.ROUNDED, border_style="blue")
    table.add_column("에이전트", style="bold cyan", width=14)
    table.add_column("평균 점수", justify="center", width=10)
    table.add_column("평가 횟수", justify="center", width=10)
    table.add_column("상태", justify="center", width=10)
    for name in AGENT_NAMES:
        hist = scores.get(name, [])
        avg = _avg(hist)
        stars = "★" * round(avg) + "☆" * (5 - round(avg))
        status = "⚠️ 교체 위험" if 0 < avg < 2.5 else ("🏆 우수" if avg >= 4.5 else "✅ 양호")
        table.add_row(name, f"{stars} ({avg})", str(len(hist)), status)
    console.print(table)


def _collect_sophie_scores():
    """프로젝트 완료 후 Sophie가 각 에이전트를 1~5점으로 평가."""
    console.print("\n[bold yellow]🎓 팀 평가 시간입니다, Sophie![/bold yellow]")
    console.print("각 에이전트가 설명을 얼마나 잘 했는지 평가해주세요.")
    console.print("[dim]기준: 질문 없이도 이해할 수 있었나요? 궁금한 걸 먼저 설명해줬나요?[/dim]\n")

    scores = _load_scores()
    for name in AGENT_NAMES:
        while True:
            raw = Prompt.ask(f"  {name} 점수 (1~5, 엔터=건너뜀)", default="")
            if raw == "":
                break
            try:
                score = int(raw)
                if 1 <= score <= 5:
                    scores[name].append(score)
                    break
                console.print("  [red]1~5 사이 숫자를 입력해주세요.[/red]")
            except ValueError:
                console.print("  [red]숫자를 입력해주세요.[/red]")

    _save_scores(scores)
    _show_team_scores(scores)


# ── 출력 헬퍼 ─────────────────────────────────────────────────────────────────
def _print_agent_output(title: str, content: str, color: str = "blue"):
    console.print(Panel(Markdown(content), title=title, border_style=color, padding=(1, 2)))


def _print_peer_reviews(reviews: list, passed: bool):
    """Peer review 결과 테이블 출력."""
    table = Table(title="🗳️ Peer Review 투표 결과", box=box.SIMPLE, border_style="cyan")
    table.add_column("에이전트", style="bold", width=14)
    table.add_column("투표", justify="center", width=8)
    table.add_column("의견", width=55)

    for r in reviews:
        vote_str = "✅ PASS" if r["vote"] == "PASS" else "❌ FAIL"
        table.add_row(r["agent"], vote_str, r.get("feedback", ""))

    pass_count = sum(1 for r in reviews if r["vote"] == "PASS")
    table.caption = f"{pass_count}/{len(reviews)} PASS → {'통과 ✅' if passed else '미통과 ❌'}"
    console.print(table)


def _ask_sophie(prompt_text: str, stage: str) -> tuple[bool, str]:
    """Sophie의 투표를 받는다 (y/n/r).

    Returns:
        (approved: bool, feedback: str)
    """
    console.print(f"\n[bold yellow]Sophie의 투표[/bold yellow] — {stage}")
    console.print("[dim]y = PASS (승인)  n = 중단  r = 수정 요청[/dim]")
    while True:
        choice = Prompt.ask(prompt_text, choices=["y", "n", "r"], default="y",
                            show_choices=True, show_default=True)
        if choice == "y":
            return True, ""
        elif choice == "n":
            console.print("[yellow]분석을 중단합니다.[/yellow]")
            sys.exit(0)
        elif choice == "r":
            feedback = Prompt.ask("어떻게 수정할까요?")
            return False, feedback


# ── 메인 실행 ─────────────────────────────────────────────────────────────────
def run(topic: str):
    from graph.graph import build_graph

    # 시작 시 팀 점수 현황 표시
    scores = _load_scores()
    if any(scores.get(n) for n in AGENT_NAMES):
        _show_team_scores(scores)
        console.print()

    graph = build_graph()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "topic": topic,
        # Planner
        "objective": None, "key_results": [], "plan": None,
        "plan_explanation": None, "plan_version": 0,
        "plan_peer_reviews": [], "plan_peer_passed": None,
        "plan_sophie_approved": None, "plan_sophie_feedback": None,
        # Researcher
        "hypothesis": None, "poc_result": None,
        "methodology": None, "methodology_explanation": None, "methodology_version": 0,
        "methodology_peer_reviews": [], "methodology_peer_passed": None,
        "methodology_sophie_approved": None, "methodology_sophie_feedback": None,
        # Analyst
        "code": None, "analysis_results": None, "code_error": None,
        "analysis_explanation": None, "analysis_iteration": 0,
        "review_passed": None, "review_feedback": None, "review_iteration": 0,
        "analysis_peer_reviews": [], "analysis_peer_passed": None,
        "analysis_sophie_approved": None, "analysis_sophie_feedback": None,
        # Reporter
        "final_report_md": None, "final_report_ppt_path": None,
        "postmortem": None, "report_explanation": None,
        "report_peer_reviews": [], "report_peer_passed": None,
        "report_sophie_approved": None, "report_sophie_feedback": None,
        # Common
        "errors": [], "is_complete": False,
    }

    console.print(f"\n[bold green]🚀 분석 시작:[/bold green] {topic}\n")

    # ── Interrupt 처리 맵 ────────────────────────────────────────────────────
    INTERRUPT_CONFIG = {
        "sophie_plan": {
            "title":       "📋 Planner — OKR + 분석 계획",
            "content_key": "plan",
            "explain_key": "plan_explanation",
            "reviews_key": "plan_peer_reviews",
            "passed_key":  "plan_peer_passed",
            "approve_key": "plan_sophie_approved",
            "feedback_key":"plan_sophie_feedback",
            "color":       "blue",
            "stage":       "분석 계획 검토",
        },
        "sophie_methodology": {
            "title":       "🔬 Researcher — 가설 + 방법론",
            "content_key": "methodology",
            "explain_key": "methodology_explanation",
            "reviews_key": "methodology_peer_reviews",
            "passed_key":  "methodology_peer_passed",
            "approve_key": "methodology_sophie_approved",
            "feedback_key":"methodology_sophie_feedback",
            "color":       "cyan",
            "stage":       "방법론 검토",
        },
        "sophie_analysis": {
            "title":       "💻 Analyst — 코드 + 분석 결과",
            "content_key": "analysis_results",
            "explain_key": "analysis_explanation",
            "reviews_key": "analysis_peer_reviews",
            "passed_key":  "analysis_peer_passed",
            "approve_key": "analysis_sophie_approved",
            "feedback_key":"analysis_sophie_feedback",
            "color":       "green",
            "stage":       "분석 결과 검토",
        },
        "sophie_report": {
            "title":       "📊 Reporter — 최종 보고서",
            "content_key": "final_report_md",
            "explain_key": "report_explanation",
            "reviews_key": "report_peer_reviews",
            "passed_key":  "report_peer_passed",
            "approve_key": "report_sophie_approved",
            "feedback_key":"report_sophie_feedback",
            "color":       "magenta",
            "stage":       "최종 보고서 검토",
        },
    }

    while True:
        for _ in graph.stream(initial_state, config, stream_mode="values"):
            pass  # 이벤트 소모

        snapshot  = graph.get_state(config)
        state     = snapshot.values
        next_nodes = snapshot.next

        if state.get("is_complete") or not next_nodes:
            console.print("\n[bold green]✅ 에이전트팀 작업 완료![/bold green]")
            # 최종 결과 경로 출력
            ppt = state.get("final_report_ppt_path")
            if ppt:
                console.print(f"[bold]📊 PPT:[/bold] {ppt}")
            break

        next_node = next_nodes[0] if next_nodes else None
        cfg = INTERRUPT_CONFIG.get(next_node)

        if cfg is None:
            console.print(f"[red]알 수 없는 중단 지점: {next_node}[/red]")
            break

        # 1. 에이전트 결과물 출력
        content = state.get(cfg["content_key"], "") or ""
        if content:
            _print_agent_output(cfg["title"], content[:2000], cfg["color"])

        # 2. Sophie 친화적 설명 출력
        explanation = state.get(cfg["explain_key"], "") or ""
        if explanation:
            console.print(Panel(
                Markdown(explanation),
                title="📚 Sophie에게",
                border_style="yellow",
                padding=(1, 2),
            ))

        # 3. Peer review 결과 출력
        reviews = state.get(cfg["reviews_key"], [])
        passed  = state.get(cfg["passed_key"], False)
        if reviews:
            _print_peer_reviews(reviews, passed)

        # 4. Sophie 투표
        approved, feedback = _ask_sophie(
            f"[y] PASS  [n] 중단  [r] 수정 요청", cfg["stage"]
        )

        graph.update_state(config, {
            cfg["approve_key"]: approved,
            cfg["feedback_key"]: feedback or None,
        })

        initial_state = None  # 이후는 체크포인터에서 상태 복원

    # 프로젝트 완료 후 Sophie 평가 수집
    _collect_sophie_scores()


def main():
    if len(sys.argv) < 2:
        console.print("[red]사용법: python main.py \"분석 주제\"[/red]")
        console.print('예시:   python main.py "고객 이탈률 분석"')
        sys.exit(1)

    topic = " ".join(sys.argv[1:])
    run(topic)


if __name__ == "__main__":
    main()
