"""Python REPL 래퍼.

Analyst 에이전트가 생성한 코드를 안전하게 실행하고 결과를 반환.
subprocess + 임시 파일 방식 사용.
"""

import os
import sys
import subprocess
import tempfile
from datetime import datetime


def execute_python(code: str, timeout: int = 60) -> dict:
    """Python 코드 실행 후 결과 반환.

    Args:
        code: 실행할 Python 코드 문자열
        timeout: 최대 실행 시간(초), 기본 60초

    Returns:
        {success, stdout, stderr, returncode, executed_at}
    """
    tmp_path = None
    try:
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            tmp_path = f.name

        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
            "executed_at": datetime.now().isoformat(),
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"실행 시간 초과 ({timeout}초). 코드를 더 작게 나누거나 데이터 크기를 줄이세요.",
            "returncode": -1,
            "executed_at": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
            "executed_at": datetime.now().isoformat(),
        }
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def get_charts_dir() -> str:
    """차트 저장 디렉토리 경로 반환 (없으면 생성)."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    charts_dir = os.path.join(base, "outputs", "charts")
    os.makedirs(charts_dir, exist_ok=True)
    return charts_dir


def build_code_header() -> str:
    """분석 코드 앞에 붙을 표준 헤더 (차트 저장 경로 설정 포함)."""
    charts_dir = get_charts_dir().replace("\\", "/")
    return f"""\
import os, sys
import warnings
warnings.filterwarnings('ignore')

import matplotlib
matplotlib.use('Agg')  # GUI 없이 파일로 저장
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CHARTS_DIR = r"{charts_dir}"
os.makedirs(CHARTS_DIR, exist_ok=True)

def save_chart(filename):
    path = os.path.join(CHARTS_DIR, filename)
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[차트 저장] {{path}}")
    return path

"""
