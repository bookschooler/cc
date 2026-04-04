"""차트 유틸리티.

outputs/charts/ 디렉토리 관리 및 차트 파일 목록 제공.
실제 차트 생성은 Analyst가 matplotlib 코드로 직접 수행.
"""

import os
import glob
from datetime import datetime


def get_charts_dir() -> str:
    """charts 디렉토리 경로 반환 (없으면 생성)."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    charts_dir = os.path.join(base, "outputs", "charts")
    os.makedirs(charts_dir, exist_ok=True)
    return charts_dir


def list_recent_charts(since_iso: str | None = None) -> list[str]:
    """최근 생성된 차트 파일 목록 반환.

    Args:
        since_iso: ISO 형식 시각 (이후 생성된 파일만). None이면 전체.

    Returns:
        차트 파일 절대 경로 목록
    """
    charts_dir = get_charts_dir()
    pattern = os.path.join(charts_dir, "*.png")
    files = glob.glob(pattern)
    if since_iso:
        cutoff = datetime.fromisoformat(since_iso).timestamp()
        files = [f for f in files if os.path.getmtime(f) >= cutoff]
    return sorted(files, key=os.path.getmtime)


def chart_paths_for_ppt(limit: int = 5) -> list[str]:
    """PPT에 삽입할 최근 차트 경로 반환 (최대 limit개)."""
    files = list_recent_charts()
    return files[-limit:] if len(files) > limit else files
