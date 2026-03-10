#!/usr/bin/env python3
"""컨설팅 에이전트팀 CLI 진입점.

사용법:
  python main.py "분석 주제"
  python main.py "삼성전자 주가 분석"
"""

import sys
import uuid
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown

load_dotenv()

console = Console()


def _print_plan(plan: str, title: str = "📋 분석 계획"):
    console.print(Panel(Markdown(plan), title=title, border_style="blue"))


def _print_mini_plan(mini_plan: str, title: str = "🔍 검색 계획"):
    console.print(Panel(mini_plan, title=title, border_style="cyan"))


def _ask_approval(prompt_text: str = "승인하시겠습니까?") -> tuple[bool, str]:
    """사용자에게 승인/거절/수정요청을 받는다.

    Returns:
        (approved: bool, feedback: str)
    """
    while True:
        choice = Prompt.ask(
            f"\n{prompt_text}",
            choices=["y", "n", "r"],
            default="y",
            show_choices=True,
            show_default=True,
        )
        if choice == "y":
            return True, ""
        elif choice == "n":
            console.print("[yellow]중단합니다.[/yellow]")
            sys.exit(0)
        elif choice == "r":
            feedback = Prompt.ask("수정 요청 내용을 입력하세요")
            return False, feedback


def run(topic: str):
    from graph.graph import build_graph

    graph = build_graph()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # 초기 상태
    initial_state = {
        "topic": topic,
        "plan": None,
        "plan_version": 0,
        "human_plan_approved": None,
        "human_plan_feedback": None,
        "searcher_mini_plan": None,
        "searcher_plan_approved": None,
        "searcher_plan_feedback": None,
        "search_results": [],
        "errors": [],
        "is_complete": False,
    }

    console.print(f"\n[bold green]🚀 분석 시작:[/bold green] {topic}\n")

    while True:
        # 그래프 실행 (interrupt까지)
        for event in graph.stream(initial_state, config, stream_mode="values"):
            pass  # stream은 상태 업데이트 이벤트를 내보냄

        # 현재 상태 확인
        snapshot = graph.get_state(config)
        state = snapshot.values
        next_nodes = snapshot.next

        # 완료 체크
        if state.get("is_complete") or not next_nodes:
            console.print("\n[bold green]✅ 에이전트팀 작업 완료![/bold green]")
            break

        # interrupt 지점에 따라 처리
        next_node = next_nodes[0] if next_nodes else None

        if next_node == "human_plan_review":
            # PM 계획 승인
            plan = state.get("plan", "")
            _print_plan(plan, f"📋 PM Agent - 분석 계획 (v{state.get('plan_version', 1)})")

            approved, feedback = _ask_approval("[y] 승인  [n] 중단  [r] 수정 요청")

            # 상태 업데이트 후 재개
            graph.update_state(
                config,
                {"human_plan_approved": approved, "human_plan_feedback": feedback or None},
            )

        elif next_node == "searcher_exec":
            # Searcher 미니플랜 승인
            mini_plan = state.get("searcher_mini_plan", "")
            _print_mini_plan(mini_plan, "🔍 Searcher Agent - 검색 계획")

            approved, feedback = _ask_approval("[y] 승인  [n] 중단  [r] 수정 요청")

            graph.update_state(
                config,
                {
                    "searcher_plan_approved": approved,
                    "searcher_plan_feedback": feedback or None,
                },
            )

        else:
            # 알 수 없는 interrupt
            console.print(f"[red]알 수 없는 중단 지점: {next_node}[/red]")
            break

        # initial_state를 None으로 설정해 이후 실행은 체크포인터 상태 사용
        initial_state = None


def main():
    if len(sys.argv) < 2:
        console.print("[red]사용법: python main.py \"분석 주제\"[/red]")
        console.print('예시:   python main.py "삼성전자 주가 분석"')
        sys.exit(1)

    topic = " ".join(sys.argv[1:])
    run(topic)


if __name__ == "__main__":
    main()
