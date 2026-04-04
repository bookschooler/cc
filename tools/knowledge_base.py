"""Knowledge Base 관리 모듈.

Obsidian 호환 마크다운 파일로 지식을 누적 저장.
구조:
  knowledge/
    index.md                  ← 전체 목록 (Obsidian graph view용)
    methodologies/<name>.md   ← 방법론별 최신 논문 + 설명 누적
    papers/<date>_<title>.md  ← ArXiv 논문 Sophie 눈높이 요약
    projects/<date>_<topic>.md ← 프로젝트별 도메인 인사이트

Obsidian 내보내기:
  knowledge/ 폴더를 Obsidian vault에 복사하면 바로 사용 가능.
  [[wikilinks]], YAML frontmatter, 태그 모두 호환.

Notion 내보내기:
  각 .md 파일을 Notion에 그대로 붙여넣기 가능 (마크다운 임포트 지원).
"""

import os
import re
from datetime import datetime

# ── 경로 설정 ──────────────────────────────────────────────────────────────────
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_DIR = os.path.join(_BASE, "knowledge")

DIRS = {
    "methodologies": os.path.join(KB_DIR, "methodologies"),
    "papers":        os.path.join(KB_DIR, "papers"),
    "projects":      os.path.join(KB_DIR, "projects"),
}


def _ensure_dirs():
    for d in DIRS.values():
        os.makedirs(d, exist_ok=True)
    os.makedirs(KB_DIR, exist_ok=True)


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _safe_name(text: str) -> str:
    """파일명 안전 변환."""
    return re.sub(r'[^\w가-힣-]', '_', text.strip())[:40]


# ── 논문 저장 ──────────────────────────────────────────────────────────────────
def save_paper(title: str, summary: str, url: str,
               methodology_tags: list[str], sophie_summary: str = "") -> str:
    """ArXiv 논문을 knowledge/papers/에 저장.

    Returns:
        저장된 파일 경로
    """
    _ensure_dirs()
    date = datetime.now().strftime("%Y%m%d")
    filename = f"{date}_{_safe_name(title)}.md"
    path = os.path.join(DIRS["papers"], filename)

    tags_yaml = ", ".join(f'"{t}"' for t in methodology_tags)
    related_links = " ".join(f"[[{t}]]" for t in methodology_tags)

    content = f"""---
title: "{title}"
type: paper
tags: [{tags_yaml}]
date: "{_today()}"
source: "{url}"
---

# {title}

> **출처:** [{url}]({url})
> **저장일:** {_today()}
> **관련 방법론:** {related_links}

## 논문 요약

{summary}

## 📚 Sophie에게 (쉬운 설명)

{sophie_summary if sophie_summary else "_이 논문이 데이터 분석에 어떻게 활용되는지 설명이 추가될 예정입니다._"}

---
*자동 생성: Researcher Agent*
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    _update_index()
    return path


# ── 방법론 저장/업데이트 ────────────────────────────────────────────────────────
def save_methodology(name: str, description: str, when_to_use: str,
                     assumptions: str, validation_methods: str,
                     recent_papers: list[str], sophie_explanation: str,
                     tags: list[str] = None) -> str:
    """방법론을 knowledge/methodologies/에 저장 (기존 파일이면 업데이트).

    Returns:
        저장된 파일 경로
    """
    _ensure_dirs()
    filename = f"{_safe_name(name)}.md"
    path = os.path.join(DIRS["methodologies"], filename)

    tags_list = tags or []
    tags_yaml = ", ".join(f'"{t}"' for t in tags_list)
    papers_md = "\n".join(f"- [[{_safe_name(p)}]] — {p}" for p in recent_papers) or "_없음_"
    update_history = ""

    # 기존 파일이 있으면 업데이트 이력 보존
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            existing = f.read()
        hist_marker = "## 업데이트 이력"
        idx = existing.find(hist_marker)
        if idx != -1:
            update_history = existing[idx:]
        update_history = f"\n- {_today()}: 업데이트됨\n" + update_history

    content = f"""---
title: "{name}"
type: methodology
tags: [{tags_yaml}]
date: "{_today()}"
---

# {name}

> 마지막 업데이트: {_today()}

## 개요

{description}

## 언제 사용하나요?

{when_to_use}

## 통계적 가정 (Statistical Assumptions)

{assumptions}

## 검증 방법 (Validation Methods)

{validation_methods}

## 관련 최신 논문

{papers_md}

## 📚 Sophie에게 (쉬운 설명)

{sophie_explanation}

## 업데이트 이력
{update_history if update_history else f"- {_today()}: 최초 생성"}

---
*자동 생성/업데이트: Researcher Agent*
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    _update_index()
    return path


# ── 프로젝트 인사이트 저장 ──────────────────────────────────────────────────────
def save_project_insight(topic: str, objective: str, key_results: list[str],
                         methodology_used: str, key_findings: str,
                         postmortem_summary: str = "") -> str:
    """프로젝트 완료 후 도메인 인사이트를 knowledge/projects/에 저장.

    Returns:
        저장된 파일 경로
    """
    _ensure_dirs()
    date = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"{date}_{_safe_name(topic)}.md"
    path = os.path.join(DIRS["projects"], filename)

    krs_md = "\n".join(f"- {kr}" for kr in key_results) or "_없음_"
    method_link = f"[[{_safe_name(methodology_used)}]]" if methodology_used else "_없음_"

    content = f"""---
title: "{topic}"
type: project
date: "{_today()}"
methodology: "{methodology_used}"
---

# {topic}

> **분석일:** {_today()}
> **사용 방법론:** {method_link}

## OKR

**Objective:** {objective}

**Key Results:**
{krs_md}

## 핵심 발견 (Key Findings)

{key_findings}

## 방법론 노트

이 프로젝트에서 {methodology_used}을(를) 사용했을 때 주의할 점:
_프로젝트 진행 중 학습한 내용이 여기에 추가됩니다._

## Blameless Post-mortem 요약

{postmortem_summary if postmortem_summary else "_아직 없음_"}

---
*자동 생성: Reporter Agent*
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    _update_index()
    return path


# ── Index 자동 갱신 ────────────────────────────────────────────────────────────
def _update_index():
    """knowledge/index.md를 현재 파일 목록 기반으로 재생성."""
    _ensure_dirs()

    def _list_section(directory: str, section_title: str) -> str:
        files = sorted(
            [f for f in os.listdir(directory) if f.endswith(".md")],
            reverse=True,
        )
        if not files:
            return f"## {section_title}\n_아직 없음_\n"
        items = "\n".join(f"- [[{f[:-3]}]]" for f in files)
        return f"## {section_title}\n{items}\n"

    methodologies_section = _list_section(DIRS["methodologies"], "📐 분석 방법론")
    papers_section        = _list_section(DIRS["papers"],        "📄 논문")
    projects_section      = _list_section(DIRS["projects"],      "🗂️ 프로젝트")

    index_content = f"""---
title: "Knowledge Base Index"
type: index
date: "{_today()}"
---

# 📚 Sophie's Knowledge Base

> 데이터 사이언스 에이전트팀이 프로젝트마다 쌓아가는 지식 저장소.
> Obsidian에서 열면 Graph View로 지식 연결을 시각화할 수 있어요.

**마지막 업데이트:** {_today()}
**총 항목 수:** {_count_all()} 개

---

{methodologies_section}
---

{papers_section}
---

{projects_section}
---

## 💡 Sophie를 위한 학습 로드맵

1. **처음이라면** → `methodologies/` 폴더의 기초 방법론부터
2. **논문이 어렵다면** → 각 파일의 "Sophie에게" 섹션만 읽기
3. **프로젝트 복습** → `projects/` 폴더에서 과거 분석 되돌아보기

---
*자동 생성: Knowledge Base 시스템*
"""
    index_path = os.path.join(KB_DIR, "index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)


def _count_all() -> int:
    total = 0
    for d in DIRS.values():
        if os.path.exists(d):
            total += len([f for f in os.listdir(d) if f.endswith(".md")])
    return total


# ── 초기화 (최초 실행 시) ─────────────────────────────────────────────────────
def init_knowledge_base():
    """knowledge/ 디렉토리 구조 초기화."""
    _ensure_dirs()
    index_path = os.path.join(KB_DIR, "index.md")
    if not os.path.exists(index_path):
        _update_index()
