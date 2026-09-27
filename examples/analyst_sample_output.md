# 📊 Analyst 샘플 출력물 — "삼성전자 주가 패턴 분析"

> 이 파일은 Analyst 에이전트가 실제로 만드는 출력물의 예시입니다.
> 코드를 실행하지 않아도 결과가 어떻게 생겼는지 먼저 볼 수 있어요.

---

## ✅ Analyst 작업 완료 보고

**분析 주제**: 삼성전자 주가와 코스피 지수 상관관계 (2023~2024)
**사용 데이터**: yfinance (005930.KS, ^KS11)
**실행 시간**: 12.4초
**생성된 파일**: `outputs/charts/samsung_vs_kospi.png`

---

## 📝 실행한 코드

```python
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

# 데이터 수집
samsung = yf.download('005930.KS', start='2023-01-01', end='2024-12-31')['Close']
kospi = yf.download('^KS11', start='2023-01-01', end='2024-12-31')['Close']

# 수익률 계산 (일별 변화율)
samsung_returns = samsung.pct_change().dropna()
kospi_returns = kospi.pct_change().dropna()

# 상관계수 계산
correlation, p_value = stats.pearsonr(samsung_returns, kospi_returns)
print(f"상관계수: {correlation:.4f}")
print(f"p-value: {p_value:.6f}")

# 차트 생성
fig, axes = plt.subplots(2, 1, figsize=(12, 8))

# 주가 추이 비교
axes[0].plot(samsung.index, samsung / samsung.iloc[0] * 100, label='삼성전자', color='blue')
axes[0].plot(kospi.index, kospi / kospi.iloc[0] * 100, label='코스피', color='red')
axes[0].set_title('삼성전자 vs 코스피 — 정규화 비교 (기준: 100)')
axes[0].legend()

# 수익률 산점도
axes[1].scatter(kospi_returns, samsung_returns, alpha=0.3, s=10)
axes[1].set_xlabel('코스피 일일 수익률')
axes[1].set_ylabel('삼성전자 일일 수익률')
axes[1].set_title(f'수익률 상관관계 (r = {correlation:.3f})')

plt.tight_layout()
plt.savefig('outputs/charts/samsung_vs_kospi.png', dpi=150)
```

---

## 📊 분析 결과

| 지표 | 값 | 의미 |
|------|-----|------|
| 피어슨 상관계수 | **0.847** | 강한 양의 상관관계 |
| p-value | **< 0.001** | 통계적으로 매우 유의미 |
| 관측 기간 | 2023.01 ~ 2024.12 | 약 2년간 데이터 |
| 데이터 포인트 수 | 487개 | 영업일 기준 |

---

## 🔢 숫자 해석 (비즈니스 언어로)

> **핵심 발견**: 삼성전자 주가는 코스피 지수 움직임의 **약 84.7%를 따라간다.**

- 코스피가 1% 오르면 삼성전자도 평균 0.89% 오른다
- 이 패턴은 통계적으로 **99.9% 이상의 신뢰도**로 유의미하다
- 단, 16% 정도는 삼성전자만의 고유 요인 (반도체 업황, 실적 발표 등)

---

## 📚 Sophie에게

안녕 Sophie! 방금 Analyst가 실제로 돌린 코드 결과예요.

어려워 보이는 숫자들을 하나씩 풀어볼게요:

**상관계수 (Correlation Coefficient: 두 변수가 얼마나 같이 움직이는지 나타내는 수치)**
- -1에서 +1 사이의 값
- +1에 가까울수록 "완전히 같이 움직인다"
- 0.847이면 "꽤 강하게 같이 움직인다" (0.7 이상이면 강한 상관관계)

**p-value (유의확률: 이 결과가 우연일 확률)**
- p < 0.001이면 "이게 우연일 가능성은 0.1% 미만" → 즉, 99.9% 이상 진짜 패턴
- "통계적으로 유의미하다"는 표현이 바로 이걸 뜻해요

**실생활 해석**: "삼성전자 주식을 살 때는 코스피 전체 분위기도 봐야 한다"

💡 **오늘의 개념**: 상관관계 (Correlation: 두 변수가 같이 움직이는 정도) ≠ 인과관계 (Causation: 원인과 결과). 코스피가 오른다고 삼성전자가 오르는 게 아니라, 두 가지가 비슷한 시장 환경의 영향을 받을 뿐이에요.
