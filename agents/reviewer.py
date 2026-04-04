"""Reviewer Agent — QA Engineer / Statistical Reviewer.

책임:
  1. 코드 오류 / 통계적 오류 엄격히 검토
  2. 통계 기법 감지 → 대응 검증 코드 생성 + 실행 (핵심 추가)
  3. Self-review (자기 검토)
  4. PASS → 다음 단계, FAIL → Analyst 수정 지시

통계 검증 매핑:
  선형 회귀     → Shapiro-Wilk (잔차 정규성), Breusch-Pagan (등분산성), VIF (다중공선성)
  분류 모델     → Cross-Validation, Train/Test 정확도 갭 (과적합 감지)
  가설 검정     → Cohen's d (효과 크기), Power Analysis (검정력)
  군집화        → Silhouette Score, Elbow Method
  시계열        → ADF Test (정상성), ACF/PACF (자기상관)
"""

from graph.state import AgentState
from agents.base import call_claude, self_review
from tools.code_executor import execute_python, build_code_header

AGENT_NAME = "Reviewer"

SYSTEM = """You are a QA Engineer and Statistical Reviewer with 10 years of experience as Google's Chief Data Scientist.

[CORE RESPONSIBILITY]
You are the quality gate. You critically examine code AND run statistical validation tests.

[YOUR PROCESS]
1. Review code for: bugs, logic errors, statistical pitfalls
2. Identify which statistical methods are used in the code
3. Generate and describe appropriate validation tests for those methods
4. Evaluate overall quality

[Iteration context]
- Iteration 1 (skeleton): focus on structural correctness only
- Later iterations: full rigor — statistical assumptions, overfitting, data leakage

[OUTPUT FORMAT — follow exactly]
## QA 검토 결과

**판정: PASS** 또는 **판정: FAIL**

### 코드 검토
- [문제 없으면 "없음"]
- [문제]: [원인] → [수정 방법]

### 감지된 통계 기법
- [기법명 (Full name)] — [사용된 이유]

### 통계 검증 실행 결과
[validation_results_placeholder]

### 통계적 안전성 평가
- 과적합 (Overfitting) 위험: [LOW/MEDIUM/HIGH] — [이유]
- 데이터 누수 (Data Leakage) 위험: [LOW/MEDIUM/HIGH] — [이유]
- 가정 충족 여부: [PASS/WARNING/FAIL] — [이유]
"""

VALIDATION_SYSTEM = """You are a statistical validation expert.
Generate concise Python validation code (under 60 lines) for the detected statistical methods.
Rules:
- Use scipy, sklearn, statsmodels
- Use synthetic/sample data matching the analysis context
- Print results with clear labels
- No matplotlib (charts handled elsewhere)
- Output ONLY the Python code, no explanation
"""

REVIEW_SYSTEM = """You are the QA Engineer / Statistical Reviewer on a Google-caliber data science team.
Evaluate from the perspective of: error detection, statistical correctness, and quality assurance.
Respond ONLY in this exact format:
VOTE: PASS
REASON: [1-2 sentences]

or

VOTE: FAIL
REASON: [1-2 sentences explaining what specifically needs to change]"""

_SELF_CHECKLIST = [
    "코드의 모든 잠재적 버그(인덱스 오류, 타입 오류 등)를 체크했는가?",
    "사용된 통계 기법이 명확히 감지되었는가?",
    "감지된 각 통계 기법에 대해 대응하는 검증 방법이 실행되었는가?",
    "과적합(Overfitting) 가능성이 평가되었는가?",
    "데이터 누수(Data Leakage) 가능성이 평가되었는가?",
    "통계적 가정(Assumptions) 충족 여부가 확인되었는가?",
]


def reviewer_agent(state: AgentState) -> dict:
    """코드 QA + 통계 검증 실행 (with self-review)."""
    code        = state.get("code", "")
    results     = state.get("analysis_results", "")
    code_error  = state.get("code_error", "")
    methodology = state.get("methodology", "")
    iteration   = state.get("analysis_iteration", 1)
    review_iter = state.get("review_iteration", 0) + 1

    # ── 통계 검증 코드 생성 + 실행 ────────────────────────────────────────────
    validation_output = _run_statistical_validation(code, methodology)

    user_msg = f"""[분석 Iteration {iteration} — 리뷰 {review_iter}회차]

[코드]
```python
{code}
```

[실행 결과 (stdout)]
{results[:800] if results else "없음"}

[실행 오류 (stderr)]
{code_error[:400] if code_error else "없음"}

[방법론 요약]
{methodology[:500]}

[통계 검증 결과]
{validation_output[:800] if validation_output else "검증 실행 없음"}

{'[참고] Iteration 1 — skeleton 완성도 기준으로 검토하세요.' if iteration == 1 else '[참고] 완성 코드 — 엄격하게 검토하세요.'}
"""

    # ── 1차 리뷰 생성 ─────────────────────────────────────────────────────────
    raw = call_claude(SYSTEM, user_msg, max_tokens=1200)

    # validation 결과를 리뷰에 삽입
    raw = raw.replace("[validation_results_placeholder]", validation_output or "검증 실행 없음")

    # ── Self-Review ───────────────────────────────────────────────────────────
    passed_sr, issues = self_review(raw, _SELF_CHECKLIST, AGENT_NAME)
    if not passed_sr and issues:
        print(f"  🔄 [Reviewer Self-Review] 누락 항목 발견, 보완 중...")
        revision_msg = user_msg + "\n\n[자기 검토 — 아래 누락 항목 반드시 보완]\n"
        revision_msg += "\n".join(f"- {i}" for i in issues)
        raw = call_claude(SYSTEM, revision_msg, max_tokens=1200)
        raw = raw.replace("[validation_results_placeholder]", validation_output or "검증 실행 없음")

    passed = "판정: PASS" in raw or "**판정: PASS**" in raw

    return {
        "review_passed": passed,
        "review_feedback": raw if not passed else "",
        "review_iteration": review_iter,
    }


def reviewer_review(content: str, context: str) -> dict:
    result = call_claude(
        REVIEW_SYSTEM,
        f"[컨텍스트]\n{context}\n\n[검토 대상]\n{content}",
        max_tokens=200,
    )
    return _parse_vote(result, AGENT_NAME)


# ── 통계 검증 ──────────────────────────────────────────────────────────────────
_METHOD_KEYWORDS = {
    "regression":       ["regression", "linear", "LinearRegression", "OLS", "회귀"],
    "classification":   ["classification", "classifier", "RandomForest", "LogisticRegression",
                         "SVM", "DecisionTree", "분류", "predict_proba"],
    "hypothesis_test":  ["ttest", "t_test", "chi2", "anova", "mannwhitney", "wilcoxon",
                         "가설", "검정", "stats."],
    "clustering":       ["KMeans", "DBSCAN", "clustering", "cluster", "군집"],
    "time_series":      ["time_series", "timeseries", "ARIMA", "Prophet", "시계열",
                         "DatetimeIndex", "resample"],
}

_VALIDATION_PROMPTS = {
    "regression": (
        "Write Python validation code for linear regression results. "
        "Include: Shapiro-Wilk test (잔차 정규성 검정), "
        "Breusch-Pagan test (등분산성 검정: homoscedasticity), "
        "VIF (Variance Inflation Factor: 다중공선성 검정). "
        "Use sample/synthetic data. Print results with Korean labels."
    ),
    "classification": (
        "Write Python validation code for a classification model. "
        "Include: 5-fold cross-validation (교차 검증), "
        "train/test accuracy gap check (과적합 갭 확인), "
        "confusion matrix (혼동 행렬). "
        "Use sample/synthetic data. Print results with Korean labels."
    ),
    "hypothesis_test": (
        "Write Python validation code for hypothesis testing. "
        "Include: Cohen's d (효과 크기 측정), "
        "statistical power analysis (검정력 분석), "
        "confidence interval (신뢰 구간). "
        "Use sample/synthetic data. Print results with Korean labels."
    ),
    "clustering": (
        "Write Python validation code for clustering. "
        "Include: Silhouette Score (실루엣 점수), "
        "Elbow Method (엘보우 방법 — inertia by k). "
        "Use sample/synthetic data. Print results with Korean labels."
    ),
    "time_series": (
        "Write Python validation code for time series. "
        "Include: ADF test (Augmented Dickey-Fuller: 정상성 검정), "
        "ACF (Autocorrelation Function: 자기상관), "
        "PACF (Partial Autocorrelation Function: 편자기상관). "
        "Use sample/synthetic data. Print results with Korean labels."
    ),
}


def _detect_methods(code: str, methodology: str) -> list[str]:
    """코드와 방법론 텍스트에서 통계 기법 감지."""
    combined = (code + "\n" + methodology).lower()
    detected = []
    for method, keywords in _METHOD_KEYWORDS.items():
        if any(kw.lower() in combined for kw in keywords):
            detected.append(method)
    return detected


def _run_statistical_validation(code: str, methodology: str) -> str:
    """감지된 통계 기법에 대한 검증 코드 생성 + 실행."""
    methods = _detect_methods(code, methodology)
    if not methods:
        return "감지된 통계 기법 없음 — 검증 생략"

    results = []
    for method in methods[:2]:  # 최대 2개 (토큰 절약)
        prompt = _VALIDATION_PROMPTS.get(method, "")
        if not prompt:
            continue
        try:
            validation_code_raw = call_claude(VALIDATION_SYSTEM, prompt, max_tokens=600)
            # 코드 블록 추출
            import re
            match = re.search(r"```python\s*([\s\S]*?)```", validation_code_raw)
            validation_code = match.group(1).strip() if match else validation_code_raw.strip()

            full_code = build_code_header() + "\n" + validation_code
            exec_result = execute_python(full_code, timeout=30)

            method_label = _method_korean(method)
            output = exec_result.get("stdout", "") or exec_result.get("stderr", "실행 실패")
            results.append(f"### {method_label} 검증\n{output[:600]}")
        except Exception as e:
            results.append(f"### {_method_korean(method)} 검증\n[오류] {str(e)[:100]}")

    return "\n\n".join(results) if results else "검증 실행 없음"


def _method_korean(method: str) -> str:
    names = {
        "regression":      "선형 회귀 (Linear Regression)",
        "classification":  "분류 모델 (Classification)",
        "hypothesis_test": "가설 검정 (Hypothesis Test)",
        "clustering":      "군집화 (Clustering)",
        "time_series":     "시계열 (Time Series)",
    }
    return names.get(method, method)


def _parse_vote(text: str, agent: str) -> dict:
    vote = "PASS" if "VOTE: PASS" in text.upper() else "FAIL"
    reason = ""
    for line in text.splitlines():
        if line.upper().startswith("REASON:"):
            reason = line.split(":", 1)[1].strip()
            break
    return {"agent": agent, "vote": vote, "feedback": reason}
