# cc/ — 데이터 분석 에이전트팀

## 팀 구성 (Google 수석 데이터 사이언티스트 기준)

| 에이전트 | 역할 | 방법론 |
|---------|------|--------|
| Planner | Lead Data Analyst — OKR 정의 + MECE 계획 | OKRs |
| Researcher | Data Science Researcher — 가설 + 방법론 설계 | Design Sprint |
| Analyst | Senior Data Scientist — 코드 작성 + 실행 | Launch and Iterate |
| Reviewer | QA Engineer — 코드/통계 검토 | Launch and Iterate |
| Reporter | Data Storyteller — PPT + 보고서 + Post-mortem | Blameless Post-mortem |

## 실행
```bash
pip install -r requirements.txt
python main.py "분석 주제"
```

## 플로우
```
planner → peer_review_plan → sophie_plan [interrupt]
→ researcher → peer_review_methodology → sophie_methodology [interrupt]
→ analyst → reviewer (loop ≤3) → peer_review_analysis → sophie_analysis [interrupt]
→ reporter → peer_review_report → sophie_report [interrupt]
→ save_output → END
```

## Peer Review
- 각 단계 완료 후 나머지 4 에이전트가 자동 투표 (PASS/FAIL)
- 4명 중 3명 이상 PASS → Sophie 투표로 이동
- Sophie (y=PASS / n=중단 / r=수정 요청)

## Sophie 점수 시스템
- 프로젝트 완료 후 각 에이전트 1~5점 평가
- 저장: `memory/agent_scores.json`
- 기준: 질문 없이 이해할 수 있었는가, 궁금한 것을 먼저 설명해줬는가

## 핵심 설계 규칙
- 모델: `claude-haiku-4-5-20251001` (토큰 절약)
- 코드 실행: subprocess + 임시 파일 (tools/code_executor.py)
- PPT 출력: python-pptx → `outputs/*.pptx`
- 차트: matplotlib → `outputs/charts/*.png`
- 체크포인터: SqliteSaver → `checkpoints.db`
- Post-mortem 누적: `memory/postmortem_log.md`

## 파일 맵
```
agents/planner.py    → OKR + MECE 계획
agents/researcher.py → Design Sprint + ArXiv + 방법론
agents/analyst.py    → 코드 작성 + REPL 실행
agents/reviewer.py   → QA 검토 (코드 + 통계)
agents/reporter.py   → PPT + MD + Post-mortem
agents/base.py       → Claude API 공통 호출
tools/search_tools.py → yfinance + firecrawl
tools/arxiv_tools.py  → ArXiv API
tools/code_executor.py → Python REPL
tools/chart_tools.py   → 차트 유틸리티
graph/state.py       → AgentState TypedDict
graph/graph.py       → StateGraph 정의
graph/router.py      → 조건부 라우팅
graph/peer_review.py → Peer review 공통 로직
main.py              → CLI 진입점 + Sophie 인터페이스
```

## 새 에이전트 추가 패턴
1. `agents/<name>.py` 생성 — `{name}_agent()` + `{name}_review()` 구현
2. `graph/state.py`에 필드 추가
3. `graph/graph.py`에 노드 추가 + interrupt 설정
4. `graph/router.py`에 라우팅 함수 추가
5. `graph/peer_review.py`의 `_get_reviewers()`에 등록
6. `main.py`의 `INTERRUPT_CONFIG`에 Sophie 표시 설정 추가
