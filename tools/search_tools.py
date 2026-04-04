"""검색 도구 모음.

현재 지원:
- yfinance: 주식/금융 데이터 (무료, API키 불필요)
  출처: Yahoo Finance (공식)
- firecrawl CLI: 웹 스크래핑 / 검색 (CLI 래퍼)

향후 추가 예정:
- FRED API (미국 경제지표)
- DART API (한국 전자공시)
- KOSIS API (통계청)
"""

import json
import subprocess
from datetime import datetime, date
from typing import Optional
import yfinance as yf


def _source(ticker: str) -> dict:
    return {
        "source_name": "Yahoo Finance",
        "source_url": f"https://finance.yahoo.com/quote/{ticker}",
        "source_type": "official_financial_data",
        "retrieved_at": datetime.now().isoformat(),
    }


def get_stock_data(ticker: str, period: str = "1y") -> dict:
    """주식/ETF 가격 데이터 조회.

    Args:
        ticker: 종목코드 (예: '005930.KS', 'AAPL', 'SPY')
        period: 기간 ('1mo', '3mo', '6mo', '1y', '2y', '5y')

    Returns:
        {ticker, period, info, recent_price, change_pct, data_points, ...출처 필드}
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)

        if hist.empty:
            return {"ticker": ticker, "error": f"데이터 없음 ({ticker})", **_source(ticker)}

        info = stock.info
        latest = hist["Close"].iloc[-1]
        oldest = hist["Close"].iloc[0]
        change_pct = ((latest - oldest) / oldest) * 100

        return {
            "ticker": ticker,
            "period": period,
            "name": info.get("longName") or info.get("shortName", ticker),
            "currency": info.get("currency", "USD"),
            "recent_price": round(float(latest), 2),
            "period_change_pct": round(float(change_pct), 2),
            "data_points": len(hist),
            "52w_high": round(float(info.get("fiftyTwoWeekHigh", 0)), 2),
            "52w_low": round(float(info.get("fiftyTwoWeekLow", 0)), 2),
            "market_cap": info.get("marketCap"),
            **_source(ticker),
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e), **_source(ticker)}


def get_multiple_stocks(tickers: list[str], period: str = "1y") -> list[dict]:
    """여러 종목 일괄 조회."""
    return [get_stock_data(t, period) for t in tickers]


def firecrawl_search(query: str, limit: int = 3) -> list[dict]:
    """웹 검색 후 페이지 본문까지 가져오기.

    Args:
        query: 검색어
        limit: 최대 결과 수 (기본 3)

    Returns:
        [{title, url, content, source_*}, ...]
    """
    try:
        result = subprocess.run(
            ["firecrawl", "search", query, "--scrape", "--limit", str(limit), "--json"],
            capture_output=True, text=True, timeout=60
        )
        data = json.loads(result.stdout)
        items = data.get("data", {}).get("web", [])
        return [
            {
                "title": item.get("title", ""),
                "content": item.get("markdown", item.get("description", "")),
                "source_name": "Firecrawl Web Search",
                "source_url": item.get("url", ""),
                "source_type": "web_search",
                "retrieved_at": datetime.now().isoformat(),
            }
            for item in items
        ]
    except Exception as e:
        return [{"error": str(e), "source_name": "Firecrawl", "source_url": "", "source_type": "web_search", "retrieved_at": datetime.now().isoformat()}]


def firecrawl_scrape(url: str) -> dict:
    """특정 URL의 페이지 본문 추출.

    Args:
        url: 스크래핑할 URL

    Returns:
        {title, content, source_*}
    """
    try:
        result = subprocess.run(
            ["firecrawl", "scrape", url, "--json"],
            capture_output=True, text=True, timeout=60
        )
        data = json.loads(result.stdout)
        return {
            "title": data.get("title", ""),
            "content": data.get("markdown", ""),
            "source_name": "Firecrawl Scrape",
            "source_url": url,
            "source_type": "web_scrape",
            "retrieved_at": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "source_name": "Firecrawl", "source_url": url, "source_type": "web_scrape", "retrieved_at": datetime.now().isoformat()}


def extract_tickers_from_plan(plan: str) -> list[str]:
    """계획 텍스트에서 ticker 후보를 추출 (간단한 파싱).

    예: '005930.KS', 'AAPL', 'SPY' 같은 패턴 탐지
    """
    import re
    # 영문+숫자+점+점 패턴 (예: 005930.KS, AAPL, USD/KRW=X)
    candidates = re.findall(r'\b([A-Z0-9]{1,6}(?:\.[A-Z]{1,2})?)\b', plan.upper())
    # 흔한 불필요 단어 필터
    stop = {"PM", "API", "SQL", "CSV", "ETF", "GDP", "IMF", "US", "KR", "USD", "KRW"}
    return [c for c in candidates if c not in stop and len(c) >= 2]
