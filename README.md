# 🚨 지금 당장 시작하는 방법 (5개월째 대기 중)

> ⛔ 이 시스템은 2026년 4월부터 Sophie를 기다리고 있습니다. 딱 3줄이면 됩니다.

## Step 1 — API 키 설정 (1분)
```bash
# .env 파일 생성 (API 키: https://console.anthropic.com 에서 무료 발급)
echo "ANTHROPIC_API_KEY=sk-ant-여기에_키_입력" > .env
```

## Step 2 — 설치 (최초 1회)
```bash
pip install -r requirements.txt
```

## Step 3 — 바로 실행
```bash
# Planner 혼자 먼저 (가장 빠름, 부담 없음)
python main.py "나의 하루 시간 관리 패턴 분석" --agent planner
```

> 결과가 나오면 Sophie가 `y`(통과) / `n`(중단) / `r`(피드백)로 결정합니다.
> 전체 팀은 준비됐을 때: `python main.py "주제"` (planner → researcher → analyst → reviewer → reporter)

---

# Claude Code 랑 놀기
클로드 코드와 놀면서 AI를 능숙하게 사용할 수 있는 사람 되기 프로젝트

## DESA (Data & Engineering Science Analysts) 팀이란?
5개의 AI 에이전트가 Sophie를 위해 데이터 분석을 해주는 시스템입니다.

| 에이전트 | 역할 |
|---------|------|
| Planner | 분석 목표(OKR) 설정 |
| Researcher | 관련 논문 + 방법론 조사 |
| Analyst | 실제 코드 작성 + 실행 |
| Reviewer | 분석 결과 검토 + QA |
| Reporter | PPT + 보고서 작성 |

## 추천 첫 주제 (쉬운 순서)
1. `"나의 스터디 일정 최적화"` — 외부 데이터 필요 없음
2. `"유튜브 알고리즘이 시청 시간에 미치는 영향"` — 논문 기반
3. `"삼성전자 주가 패턴 분석"` — 실시간 데이터
