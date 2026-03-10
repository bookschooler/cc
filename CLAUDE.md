# 컨설팅 에이전트팀 - CLAUDE.md

이 파일은 Claude Code가 프로젝트 컨텍스트를 유지하기 위한 파일입니다.

## 프로젝트 목적

LangGraph + Claude API 기반 **데이터 분석 컨설팅 에이전트팀** MVP.
경제/금융 주제를 입력하면 에이전트들이 협력해 데이터를 수집하고 분석 계획을 작성한다.

## 실행 방법

```bash
cd cc/
pip install -r requirements.txt

# .env 파일에 ANTHROPIC_API_KEY 설정 (상위 디렉토리에 있어도 됨)
python main.py "분석 주제"
# 예: python main.py "삼성전자 주가 분석"
```

## 현재 에이전트 플로우 (MVP)

```
[사용자 입력: 분석 주제]
        ↓
   PM Agent → 분석 계획 생성 (Claude Haiku)
        ↓
   [Human Approval] ← y/n/r 입력
        ↓
   Searcher Agent → 미니플랜 제시
        ↓
   [Human Approval] ← y/n/r 입력
        ↓
   Searcher Agent → 데이터 수집 (yfinance)
        ↓
   outputs/ 에 JSON 저장
```

## 파일 구조

```
cc/
├── main.py                 # CLI 진입점
├── requirements.txt
├── graph/
│   ├── state.py            # AgentState TypedDict
│   ├── graph.py            # LangGraph StateGraph (interrupt 포함)
│   └── router.py           # 조건부 라우팅
├── agents/
│   ├── base.py             # Claude Haiku 호출 공통
│   ├── pm.py               # PM Agent (계획 생성)
│   └── searcher.py         # Searcher (미니플랜 → 실행)
└── tools/
    └── search_tools.py     # yfinance (무료, 출처 포함)
```

## 주요 설계 원칙

- **토큰 절약**: claude-haiku-4-5-20251001 사용, MCP보다 CLI 우선
- **Plan Approval**: 각 에이전트 실행 전 사람 승인 필수 (y/n/r)
- **출처 표기**: Searcher는 신뢰 출처만 + source_url 필수
- **체크포인터**: SqliteSaver → 세션 재개 가능 (`checkpoints.db`)

## 다음 단계 (TODO)

1. **Critic Agent** 추가 (계획 자동 검증, 점수 부여)
2. **Analyst Agent** 추가 (pandas 분석, matplotlib 차트)
3. **Designer Agent** 추가 (python-pptx 보고서)
4. **Supabase 연결** (memory/store.py - 에이전트 학습 저장)
5. **FRED API** 추가 (미국 경제지표)
6. **DART API** 추가 (한국 전자공시)
7. **KOSIS API** 추가 (통계청)
8. **firecrawl CLI** 연동 (웹 스크래핑)

## 기술 스택

- LangGraph >= 0.2.0 (StateGraph, interrupt_before, SqliteSaver)
- anthropic >= 0.40.0 (Claude Haiku)
- yfinance (Yahoo Finance 데이터)
- rich (터미널 UI)

## 환경변수

```env
# 필수
ANTHROPIC_API_KEY=sk-ant-...

# 다음 단계에서 추가
# SUPABASE_URL=
# SUPABASE_KEY=
# FRED_API_KEY=
# DART_API_KEY=
# KOSIS_API_KEY=
# TAVILY_API_KEY=
```
