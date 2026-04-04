"""ArXiv API 래퍼.

학술 논문 검색 (API 키 불필요, 무료).
데이터 사이언스 / 통계 / ML 방법론 탐색에 사용.
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime


_NS = {"atom": "http://www.w3.org/2005/Atom"}
_API_URL = "http://export.arxiv.org/api/query"


def search_arxiv(query: str, max_results: int = 3) -> list[dict]:
    """ArXiv에서 논문 검색.

    Args:
        query: 검색어 (예: "time series forecasting LSTM")
        max_results: 최대 결과 수

    Returns:
        [{title, summary, url, source_*}, ...]
    """
    try:
        resp = requests.get(
            _API_URL,
            params={
                "search_query": f"all:{query}",
                "max_results": max_results,
                "sortBy": "relevance",
                "sortOrder": "descending",
            },
            timeout=30,
        )
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        papers = []
        for entry in root.findall("atom:entry", _NS):
            title_el = entry.find("atom:title", _NS)
            summary_el = entry.find("atom:summary", _NS)
            id_el = entry.find("atom:id", _NS)
            papers.append({
                "title": (title_el.text or "").strip(),
                "summary": (summary_el.text or "").strip()[:600],
                "source_name": "ArXiv",
                "source_url": (id_el.text or "").strip(),
                "source_type": "academic_paper",
                "retrieved_at": datetime.now().isoformat(),
            })
        return papers
    except Exception as e:
        return [{"error": str(e), "source_name": "ArXiv", "source_url": "", "source_type": "academic_paper", "retrieved_at": datetime.now().isoformat()}]


def format_papers_for_prompt(papers: list[dict]) -> str:
    """논문 목록을 프롬프트용 텍스트로 변환."""
    if not papers:
        return "검색 결과 없음"
    lines = []
    for i, p in enumerate(papers, 1):
        if "error" in p:
            lines.append(f"{i}. [오류] {p['error']}")
        else:
            lines.append(f"{i}. {p['title']}\n   요약: {p['summary'][:300]}\n   URL: {p['source_url']}")
    return "\n\n".join(lines)
