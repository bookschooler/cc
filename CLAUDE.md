> Last auto-reviewed: 2026-08-16

# DESA — Data & Engineering Science Analysts

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

python main.py "분석 주제"                    # DESA 전체 팀
python main.py "주제" --agent planner         # Planner만 단독 실행
python main.py "주제" --agent researcher      # Researcher만 단독 실행
python main.py "주제" --agent analyst         # Analyst만 단독 실행
python main.py "주제" --agent reviewer        # Reviewer만 단독 실행
python main.py "주제" --agent reporter        # Reporter만 단독 실행
python main.py "주제" --from researcher       # Researcher부터 끝까지
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

## 시스템 건강 규칙 (2026-08-09 추가)

### 코드 품질
- `main.py` 수정 후 반드시 `python -c "import ast; ast.parse(open('main.py').read()); print('OK')"` 실행
- `graph/graph.py` 수정 후 `python -c "from graph.graph import build_graph; print('OK')"` 실행
- 리팩토링 시 불필요한 코드 블록(고아 딕셔너리, 미사용 변수)이 함수 내에 남지 않도록 주의

### 레거시 파일 관리
- `agents/pm.py`, `agents/searcher.py` 는 초기 아키텍처 잔재 — 현재 `AgentState`에 없는 필드를 참조하므로 현재 그래프에서 사용하지 말 것
- 새 파일 추가 시 반드시 `graph/state.py`에 대응 필드를 먼저 추가하고, `graph/graph.py` 노드에도 등록할 것
- 파일맵(`## 파일 맵` 섹션)을 항상 최신 상태로 유지할 것

### Sophie 친화적 출력 규칙
- 모든 에이전트의 `## 📚 Sophie에게` 섹션은 필수 — 건너뛰면 Self-Review FAIL
- 전문용어 첫 등장 시: 반드시 `한국어명 (영문 Full Name: 한글 풀이)` 형식으로 표기
- 숫자 결과는 비즈니스 언어로 변환: `p=0.003` → `통계적으로 99.7% 신뢰도로 유의미한 차이`
- 마지막 줄에 `💡 오늘의 개념:` 포함 필수

### Sophie 성장 추적
- 프로젝트 완료마다 `memory/sophie_progress.md`의 체크리스트 항목 업데이트
- Sophie가 r(수정 요청)을 선택한 경우: 수정 내용을 `memory/feedback_{날짜}.md`에 기록
- 점수 3점 이하 에이전트가 2회 연속이면 해당 에이전트의 Sophie 설명 프롬프트 강화 검토

### 첫 실행 전 체크리스트
- [ ] `.env` 파일에 `ANTHROPIC_API_KEY` 설정 확인
- [ ] `pip install -r requirements.txt` 완료
- [ ] `python -c "import ast; ast.parse(open('main.py').read()); print('OK')"` → OK
- [ ] `python main.py "테스트 주제" --agent planner` 로 단독 실행 테스트 먼저

## Sophie를 위한 첫걸음 가이드 (2026-08-16 추가)

> ⚠️ **시스템이 두 달째 대기 중입니다.** 시스템은 완성되어 있어요. 딱 한 줄만 입력하면 됩니다!

### 🟢 지금 당장 시작하는 3단계

**Step 1 — API 키 확인 (30초)**
```bash
cat .env | grep ANTHROPIC
# ANTHROPIC_API_KEY=sk-ant-... 이 보이면 OK
```

**Step 2 — Planner 혼자 먼저 (부담 없이)**
```bash
python main.py "나의 하루 시간 관리 패턴 분석" --agent planner
```
Planner 하나만 실행합니다. 전체 팀을 다 돌릴 필요 없어요.
Sophie 인터페이스에서 `y` 누르면 통과, `n` 누르면 중단, `r`로 피드백.

**Step 3 — 전체 팀 (준비가 됐을 때)**
```bash
python main.py "삼성전자 주가와 반도체 수출 상관관계"
```

### Sophie 추천 첫 주제 (쉬운 순서)
1. `"나의 스터디 일정 최적화"` — 외부 데이터 필요 없음, 빠름
2. `"유튜브 알고리즘이 시청 시간에 미치는 영향"` — 논문 기반 분석
3. `"삼성전자 주가 패턴 분석"` — yfinance 실시간 데이터

### 처음 실행 시 Sophie가 볼 화면 예시
```
✅ [Planner] OKR 계획 완성
🗳️  Peer Review 진행 중... [Researcher: PASS] [Analyst: PASS] ...
📋 Sophie 검토 차례입니다!
---
[Sophie에게] ...
---
계속하려면 y, 중단은 n, 수정 요청은 r: 
```
`y`를 누르면 다음 단계로 넘어갑니다. 어렵지 않아요!

## 시스템 활성화 진단 규칙 (2026-08-16 추가)

### 주간 리뷰에서 체크할 항목
- `agent_scores.json` 모든 배열이 비어있으면: **Sophie에게 첫 프로젝트 실행 독려 메시지 작성**
- `memory/postmortem_log.md`에 내용이 없으면: 시스템이 아직 실제로 사용된 적 없음
- `memory/sophie_progress.md`의 누적 프로젝트 수 = 0 이 2주 연속이면: 활성화 장벽 원인 분석 필요

### 비활성화 원인 탐지 순서
1. `.env` 파일 존재 여부 (`cat .env`)
2. `ANTHROPIC_API_KEY` 설정 여부
3. `requirements.txt` 설치 여부 (`pip list | grep anthropic`)
4. `main.py` 구문 오류 여부 (AST 파싱 체크)
