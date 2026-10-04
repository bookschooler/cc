"""DESA Streamlit 웹 인터페이스

브라우저에서 클릭 한 번으로 DESA 에이전트팀 실행.
터미널 없이도 Sophie가 바로 시작할 수 있는 GUI 진입점.

실행 방법:
    pip install streamlit
    streamlit run app.py
"""

import os
import json
import subprocess
import sys
import streamlit as st
from pathlib import Path

# ── 페이지 설정 ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DESA — 데이터 분석 팀",
    page_icon="📊",
    layout="centered",
)

# ── 경로 설정 ─────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
SCORES_PATH = BASE_DIR / "memory" / "agent_scores.json"
ENV_PATH = BASE_DIR / ".env"

AGENT_NAMES = ["Planner", "Researcher", "Analyst", "Reviewer", "Reporter"]
AGENT_DESCS = {
    "Planner": "OKR 목표 설정 + MECE 분석 계획",
    "Researcher": "가설 설계 + 방법론 + 논문 조사",
    "Analyst": "Python 코드 작성 + 실제 데이터 분석",
    "Reviewer": "코드 검토 + 통계 검증 QA",
    "Reporter": "PPT 보고서 + 시각화 + Post-mortem",
}

SAMPLE_TOPICS = [
    "나의 하루 시간 관리 패턴 분석",
    "유튜브 알고리즘이 시청 시간에 미치는 영향",
    "삼성전자 주가와 반도체 수출 상관관계",
    "스터디 일정 최적화",
    "커피 섭취와 생산성의 관계",
]

# ── 헬퍼 함수 ─────────────────────────────────────────────────────────────────

def load_scores() -> dict:
    if SCORES_PATH.exists():
        with open(SCORES_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {name: [] for name in AGENT_NAMES}


def avg(lst: list) -> float:
    return round(sum(lst) / len(lst), 2) if lst else 0.0


def check_env() -> bool:
    """ANTHROPIC_API_KEY 환경변수 존재 여부 확인."""
    if ENV_PATH.exists():
        content = ENV_PATH.read_text()
        return "ANTHROPIC_API_KEY" in content and "여기에" not in content
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


# ── UI 시작 ───────────────────────────────────────────────────────────────────

st.title("📊 DESA — 데이터 분석 팀")
st.caption("Data & Engineering Science Analysts · Sophie를 위한 AI 데이터 사이언스 팀")

st.divider()

# API 키 상태 배너
env_ok = check_env()
if not env_ok:
    st.error(
        "⛔ **API 키가 설정되지 않았습니다.**\n\n"
        "아래 **'설정'** 탭에서 Anthropic API 키를 입력해주세요.\n\n"
        "API 키 발급 (무료 시작): https://console.anthropic.com"
    )
else:
    st.success("✅ API 키 확인 완료 — 지금 바로 실행할 수 있어요!")

st.divider()

# ── 탭 레이아웃 ───────────────────────────────────────────────────────────────
tab_run, tab_samples, tab_scores, tab_settings = st.tabs(
    ["🚀 실행", "📚 샘플 보기", "📈 팀 성과", "⚙️ 설정"]
)

# ── 탭 1: 실행 ────────────────────────────────────────────────────────────────
with tab_run:
    st.subheader("분석 주제 입력")

    col_topic, col_example = st.columns([3, 1])
    with col_example:
        st.write("")
        st.write("")
        if st.button("💡 예시 주제"):
            import random
            st.session_state["topic"] = random.choice(SAMPLE_TOPICS)

    with col_topic:
        topic = st.text_input(
            "어떤 주제를 분석할까요?",
            value=st.session_state.get("topic", ""),
            placeholder="예: 나의 하루 시간 관리 패턴 분석",
            key="topic_input",
        )

    st.write("")
    st.subheader("실행 방식 선택")

    run_mode = st.radio(
        "어떻게 실행할까요?",
        options=["🟢 Planner만 (빠름, 추천)", "🔵 전체 팀 (Planner → Reporter)"],
        index=0,
        help="처음이라면 Planner만 먼저 실행해보세요. 약 1~2분이면 결과가 나와요.",
    )

    st.write("")

    with st.expander("고급 옵션: 특정 에이전트만 실행"):
        selected_agent = st.selectbox(
            "단독 실행할 에이전트",
            options=["(선택 안 함)"] + AGENT_NAMES,
        )
        from_agent = st.selectbox(
            "이 에이전트부터 끝까지 실행",
            options=["(선택 안 함)"] + AGENT_NAMES,
        )

    st.write("")

    if st.button("▶️ 분석 시작", type="primary", disabled=not env_ok or not topic):
        if not topic.strip():
            st.warning("분석 주제를 입력해주세요.")
        else:
            # 명령어 구성
            cmd = [sys.executable, str(BASE_DIR / "main.py"), topic]

            if selected_agent != "(선택 안 함)":
                cmd += ["--agent", selected_agent.lower()]
            elif from_agent != "(선택 안 함)":
                cmd += ["--from", from_agent.lower()]
            elif "Planner만" in run_mode:
                cmd += ["--agent", "planner"]

            st.info(f"실행 명령어: `{' '.join(cmd[2:])}`")
            st.warning(
                "⚠️ **Streamlit에서는 터미널 인터랙티브 모드(y/n/r)가 작동하지 않아요.**\n\n"
                "아래 명령어를 터미널에 붙여넣어 실행하세요:"
            )
            st.code(" ".join(cmd), language="bash")

            st.info(
                "📌 Jupyter Notebook에서도 실행 가능해요:\n```\n"
                "jupyter notebook notebooks/quick_start.ipynb\n```"
            )

# ── 탭 2: 샘플 보기 ───────────────────────────────────────────────────────────
with tab_samples:
    st.subheader("📚 에이전트 출력 예시")
    st.write("실행 전에 미리 결과물을 구경해보세요.")

    examples_dir = BASE_DIR / "examples"
    sample_files = {
        "Planner": "planner_sample_output.md",
        "Researcher": "researcher_sample_output.md",
        "Analyst": "analyst_sample_output.md",
        "Reviewer": "reviewer_sample_output.md",
        "Reporter": "reporter_sample_output.md",
    }

    selected_sample = st.selectbox("에이전트 선택", list(sample_files.keys()))
    sample_path = examples_dir / sample_files[selected_sample]

    if sample_path.exists():
        content = sample_path.read_text(encoding="utf-8")
        st.markdown(content)
    else:
        st.warning(f"샘플 파일이 아직 없어요: `{sample_files[selected_sample]}`")

# ── 탭 3: 팀 성과 ─────────────────────────────────────────────────────────────
with tab_scores:
    st.subheader("📈 Sophie의 팀 성과 평가")

    scores = load_scores()
    for name in AGENT_NAMES:
        hist = scores.get(name, [])
        a = avg(hist)
        stars = "★" * round(a) + "☆" * (5 - round(a))
        label = f"**{name}** — {AGENT_DESCS[name]}"
        if not hist:
            st.write(f"{label}  \n점수 없음 (아직 실행되지 않았어요)")
        else:
            st.write(f"{label}  \n{stars} ({a}점 / {len(hist)}회 평가)")
        st.progress(a / 5.0 if a else 0.0)

    if all(not scores.get(n) for n in AGENT_NAMES):
        st.info("첫 프로젝트를 완료하면 여기에 Sophie의 평가가 기록돼요!")

# ── 탭 4: 설정 ────────────────────────────────────────────────────────────────
with tab_settings:
    st.subheader("⚙️ API 키 설정")

    st.write(
        "Anthropic API 키가 필요해요. 첫 가입 시 **무료 크레딧**이 제공됩니다.\n\n"
        "1. https://console.anthropic.com 에서 회원가입 (약 2분)\n"
        "2. 'Get API keys' → 'Create Key'\n"
        "3. 아래에 붙여넣기"
    )

    api_key_input = st.text_input(
        "ANTHROPIC_API_KEY",
        type="password",
        placeholder="sk-ant-...",
    )

    if st.button("💾 저장"):
        if api_key_input.startswith("sk-ant-"):
            env_content = f"ANTHROPIC_API_KEY={api_key_input}\n"
            ENV_PATH.write_text(env_content)
            st.success("✅ API 키가 저장됐어요! 페이지를 새로고침하면 실행할 수 있어요.")
        else:
            st.error("올바른 API 키 형식이 아니에요. 'sk-ant-'로 시작해야 합니다.")

    st.divider()
    st.subheader("현재 상태")

    col1, col2, col3 = st.columns(3)
    scores = load_scores()
    total_runs = sum(len(v) for v in scores.values())

    col1.metric("API 키", "✅ 설정됨" if env_ok else "❌ 미설정")
    col2.metric("누적 프로젝트", f"{total_runs // len(AGENT_NAMES)}개")
    col3.metric("팀 평균 점수", f"{avg([s for v in scores.values() for s in v])}점")
