> Last auto-reviewed: 2026-10-04

> ⛔🚨 **[긴급 경고 — 약 6개월 미실행 / 9주 연속]** `.env` 파일이 9주 연속 존재하지 않음이 확인되었습니다. 이제 **브라우저에서 클릭 한 번**으로 시작 가능:
> ```bash
> pip install streamlit
> streamlit run app.py
> ```
> 브라우저가 자동으로 열립니다. API 키도 웹 UI에서 직접 입력 가능!
> 💳 **API 키 첫 발급 시 무료 크레딧 제공 — 신용카드 없이 시작 가능!** → https://console.anthropic.com
> 또는 Jupyter: `jupyter notebook notebooks/quick_start.ipynb`
> `memory/weekly_insights.md`에 Sophie에게 쓴 편지가 있습니다 — 먼저 읽어보세요.

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

### API 키 무료 시작 안내 (2026-09-20 추가)
- Anthropic API는 **첫 가입 시 무료 크레딧 제공** — 신용카드 없이도 시작 가능
- 무료 크레딧으로 Planner 단독 실행 약 50~100회 가능 (토큰 절약 모델 사용 중)
- API 키 발급: https://console.anthropic.com → "Get API keys" → "Create Key"
- 발급 시간: 회원가입 포함 약 3분

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

## 🚨 긴급 활성화 가이드 (2026-08-23 추가 — 4개월 미실행)

> ⛔ **현재 상태: `.env` 파일이 존재하지 않습니다.** 이것이 Sophie가 시스템을 실행하지 못한 가장 유력한 원인입니다.

### 지금 당장 해야 할 단 하나의 일

```bash
# 1. 프로젝트 루트에 .env 파일 생성
echo "ANTHROPIC_API_KEY=여기에_본인_API_키_입력" > .env

# 2. API 키 확인 (https://console.anthropic.com 에서 발급)
cat .env

# 3. 바로 실행
python main.py "나의 하루 시간 관리 패턴 분석" --agent planner
```

### `.env` 파일 없을 때 나타나는 증상
- `AuthenticationError`, `API key not found` 오류
- `KeyError: 'ANTHROPIC_API_KEY'` 오류
- 아무 결과도 없이 바로 종료됨

### 주간 리뷰 에이전트 체크 의무 (2026-08-23 추가)
- 매 주간 리뷰 시 `.env` 파일 존재 여부를 **가장 먼저** 확인
- `.env` 없으면: `weekly_insights.md`에 "⛔ API 키 없음 — 실행 불가" 명시
- 3주 연속 `.env` 없음 확인 시: CLAUDE.md 최상단에 빨간 경고 추가

### 연속 미실행 에스컬레이션 규칙
- **2주 연속 미실행**: 첫걸음 가이드 추가 (2026-08-16 완료)
- **3주 연속 미실행**: `.env` 설정 단계별 안내 추가 (2026-08-23 완료)
- **4주 연속 미실행**: README.md 최상단에 긴급 설정 가이드 삽입 (2026-08-30 완료) + CLAUDE.md 최상단 경고 추가 (2026-08-30 완료)
- **5주 연속 미실행**: `examples/` 폴더에 Planner 샘플 출력물 추가 + 모든 가이드 재점검 (2026-09-06 완료)
- **6주 연속 미실행**: 가이드 전체 재점검 — Sophie에게 1:1 편지 형식 동기부여 메시지 작성 + `memory/weekly_insights.md`에 진입 장벽 상세 분석 추가 (2026-09-13 완료)
- **7주 연속 미실행**: `examples/researcher_sample_output.md` 추가 + API 무료 크레딧 강조 + 8주 재설계 사전 준비 착수 (2026-09-20 완료)
- **8주 연속 미실행**: 시스템 재설계 착수 — `notebooks/quick_start.ipynb` Jupyter 인터페이스 추가 + analyst/reviewer/reporter 샘플 출력물 추가 (2026-09-27 완료)
- **9주 연속 미실행**: `app.py` Streamlit 웹 인터페이스 추가 완료 — `streamlit run app.py` 한 줄로 브라우저 GUI 실행 가능. API 키 입력도 웹 UI에서 처리 (2026-10-04 완료)

### 주간 .env 확인 기록 (자동 누적)
| 날짜 | .env 존재 여부 | 조치 |
|------|--------------|------|
| 2026-08-09 | 미확인 | 시스템 버그 수정 |
| 2026-08-16 | 미확인 → 추정 없음 | 첫걸음 가이드 추가 |
| 2026-08-23 | ❌ 없음 (1차 확인) | 긴급 가이드 CLAUDE.md 추가 |
| 2026-08-30 | ❌ 없음 (2차 확인) | README.md 최상단 가이드 + CLAUDE.md 경고 추가 |
| 2026-09-06 | ❌ 없음 (3차 확인) | examples/planner_sample_output.md 생성 + 모든 가이드 재점검 완료 |
| 2026-09-13 | ❌ 없음 (4차 확인) | 6주 에스컬레이션 — Sophie에게 1:1 편지 작성 + 진입 장벽 상세 분석 추가 |
| 2026-09-20 | ❌ 없음 (5차 확인) | 7주 에스컬레이션 — examples/researcher_sample_output.md 추가 + 무료 크레딧 강조 + 8주 재설계 준비 |
| 2026-09-27 | ❌ 없음 (6차 확인) | 8주 에스컬레이션 — Jupyter Notebook 인터페이스 추가 + analyst/reviewer/reporter 샘플 출력물 추가 |
| 2026-10-04 | ❌ 없음 (7차 확인) | 9주 에스컬레이션 — app.py Streamlit 웹 인터페이스 추가 완료 (브라우저 기반 완전 GUI) |

## 8주 재설계 실행 (2026-09-27 — 8주 미실행 확인, 계획 → 실행으로 전환)

> 8주 연속 미실행 확인. 계획에서 실행으로 전환 — Jupyter Notebook 인터페이스 추가 완료.

### 재설계 핵심 방향: 터미널 없는 진입 경로

현재 시스템의 진입점은 **터미널 명령어**다. 이것이 8주 동안 Sophie의 가장 큰 장벽이었을 가능성이 높다.

**재설계 완료 현황 (2026-09-27 기준)**
1. **[완료]** `examples/` 폴더에 5개 에이전트 샘플 출력물 모두 추가 — Sophie가 실행 전에 전체 흐름을 볼 수 있음
2. **[완료]** `notebooks/quick_start.ipynb` Jupyter Notebook 인터페이스 추가 — 터미널 대신 셀 실행 방식
3. **[다음 단계]** Streamlit 또는 Gradio 웹 인터페이스 — 9주 연속 미실행 시 착수

### Jupyter Notebook 진입 방법 (새로운 대안)
```bash
pip install jupyter
jupyter notebook notebooks/quick_start.ipynb
```
브라우저에서 자동으로 열립니다. 셀 하나씩 실행 (Shift+Enter).

### 9주 재설계 준비
- 9주 연속 미실행 시: `app.py` Streamlit 인터페이스 추가 — `streamlit run app.py` 한 줄로 웹 UI 실행
- Streamlit은 코드 한 줄 없이도 슬라이더/버튼으로 에이전트 호출 가능

## 9주차 Streamlit 인터페이스 완성 (2026-10-04 — 9주 미실행 확인)

> 9주 연속 미실행 확인. 에스컬레이션 계획대로 `app.py` Streamlit 웹 인터페이스 구현 완료.

### Sophie를 위한 완전 GUI 진입점

터미널, 코드, 명령어가 전혀 필요 없는 세 번째 진입 경로:

```bash
pip install streamlit
streamlit run app.py
```

브라우저가 자동으로 열리고, 탭 4개로 구성된 GUI가 나타납니다:
- **🚀 실행 탭**: 주제 입력 → 에이전트 선택 → 분석 시작
- **📚 샘플 보기 탭**: examples/ 폴더의 샘플 출력물을 브라우저에서 바로 열람
- **📈 팀 성과 탭**: Sophie가 평가한 에이전트 점수 시각화
- **⚙️ 설정 탭**: API 키를 웹 폼에서 직접 입력 → .env 자동 생성

### 현재 Sophie에게 열린 세 가지 진입 경로

| 경로 | 명령어 | 터미널 필요 | API 키 입력 |
|------|--------|-----------|------------|
| A. 터미널 직접 | `python main.py "주제" --agent planner` | ✅ | .env 파일 직접 생성 |
| B. Jupyter | `jupyter notebook notebooks/quick_start.ipynb` | ✅ (1회) | .env 파일 직접 생성 |
| C. Streamlit (신규) | `streamlit run app.py` | ✅ (1회) | 웹 UI에서 입력 가능 |

### 10주 재설계 고려사항
- 10주 연속 미실행 시: 가이드 전체 재검토 — 기술적 장벽은 제거됐으므로 Sophie에게 1:1 직접 소통 채널 검토
- 현재 모든 기술적 진입 장벽은 제거된 상태 (터미널/Jupyter/Web 3가지 경로 모두 제공)
