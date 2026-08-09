# Weekly Insights — 2026-08-09

> DESA 주간 자동 리뷰 | 이번 주는 시스템 구축 이후 첫 번째 자동 리뷰입니다.

---

## 이번 주 핵심 발견 (Top 3 Insights)

### 1. 🚨 치명적 버그 발견 및 수정 — main.py 실행 불가 상태였음
`main.py`의 `_run_graph_loop` 함수 안에 고아 딕셔너리(orphaned dict)가 존재해
`IndentationError`가 발생, 시스템이 전혀 실행되지 않는 상태였습니다.

**원인**: 리팩토링 과정에서 `initial_state = {` 라인이 삭제됐지만 딕셔너리 본문은 남았습니다.
**조치**: 해당 고아 딕셔너리 블록 제거. `_run_graph_loop`은 `initial_state`를 파라미터로 받으므로 내부 정의 불필요.
**검증**: `python -c "import ast; ast.parse(open('main.py').read()); print('OK')"` → OK 확인.

### 2. 📁 레거시 파일 2개가 현재 아키텍처와 불일치
`agents/pm.py`와 `agents/searcher.py`는 초기 아키텍처(Phase 1)의 잔재입니다.
이 파일들은 `AgentState`에 없는 필드(`human_plan_feedback`, `searcher_mini_plan` 등)를 참조하며,
현재 그래프(`graph/graph.py`)에 등록되어 있지 않아 실제로는 호출되지 않습니다.
오해를 방지하기 위해 CLAUDE.md에 레거시 파일 관리 규칙을 추가했습니다.

### 3. 📊 아직 실제 프로젝트 실행 0회 — 기준선 데이터 없음
`agent_scores.json`, `postmortem_log.md`, `knowledge/index.md` 모두 비어있습니다.
점수, 병목, 피드백 패턴을 분석하려면 **최소 1~2회의 실제 프로젝트 실행이 필요**합니다.
이번 리뷰는 시스템 구조 점검에 집중했습니다.

---

## 에이전트 성과 트렌드

| 에이전트 | 누적 점수 | 평가 횟수 | 비고 |
|---------|---------|---------|------|
| Planner | - | 0 | 데이터 없음 |
| Researcher | - | 0 | 데이터 없음 |
| Analyst | - | 0 | 데이터 없음 |
| Reviewer | - | 0 | 데이터 없음 |
| Reporter | - | 0 | 데이터 없음 |

> **다음 주 목표**: 최소 1회 프로젝트 완료 후 에이전트별 Sophie 점수 확보

각 에이전트 코드를 검토한 결과:
- **Planner**: OKR + MECE 구조 잘 잡혀있음. Sophie 섹션 Self-Review 체크리스트 5항목 완비.
- **Reporter**: 가장 복잡한 에이전트 (PPT + MD + KB + Post-mortem). max_tokens=2000으로 다른 에이전트(1024~1200)보다 큼 — 토큰 사용 주의.
- **모든 에이전트**: Self-Review 로직 포함 — FAIL 시 자동 재생성. 잘 설계된 안전장치.

---

## Sophie 성장 포인트

**현재 상태**: 시스템 준비 완료, 아직 첫 프로젝트 미실행.

**Sophie가 첫 프로젝트에서 배울 핵심 개념 3가지**:

1. **OKR (Objectives and Key Results)**: Planner가 맨 먼저 보여줄 개념. "왜 이 분석을 하는가?"를 숫자로 정의하는 방법. 예) "매출 20% 향상"이 Objective, "신규 고객 월 500명 확보"가 Key Result.

2. **MECE 구조**: 분석 계획이 서로 겹치지 않고 전체를 커버하는지 확인하는 원칙. 처음엔 어려워 보여도 Planner가 Sophie 섹션에서 쉽게 설명해줄 예정.

3. **Blameless Post-mortem**: 프로젝트 마지막에 Reporter가 작성. "누구의 잘못인가?"가 아닌 "시스템을 어떻게 더 좋게 만들까?"에 집중. Sophie도 같은 방식으로 피드백을 주면 좋습니다.

**Sophie를 위한 첫 프로젝트 추천 주제**:
- `python main.py "삼성전자 주가와 반도체 수출 상관관계"` — 관심 주제가 없다면 이걸로 시작!
- 먼저 단독 실행으로 익숙해지기: `python main.py "삼성전자 주가" --agent planner`

---

## 다음 주 개선 권고

- **[필수] 첫 프로젝트 실행**: 단독 에이전트부터 시작해 시스템 동작 확인
  ```bash
  python main.py "삼성전자 주가 분석" --agent planner
  ```
- **[필수] .env 파일 설정 확인**: `ANTHROPIC_API_KEY`가 없으면 시스템이 시작조차 안 됩니다
- **[권고] 레거시 파일 정리 결정**: `agents/pm.py`, `agents/searcher.py`를 `archive/` 폴더로 이동하거나 삭제 — 현재 그래프에서 사용되지 않음
- **[권고] Reviewer max_tokens 확인**: 현재 코드 검토 후 통계 QA까지 1024 토큰이 충분한지 실행 후 점검
- **[모니터링] Self-Review 효과 측정**: 첫 실행 시 콘솔에 `🔄 [에이전트명 Self-Review] 문제 발견, 수정 중...` 메시지가 얼마나 발생하는지 관찰

---

*자동 생성: DESA 주간 리뷰 루틴 | 2026-08-09*
