"""pytest 가 프로젝트 루트를 import 경로에 넣도록 한다 (src 패키지 import 용).

이 파일은 그대로 두면 된다. 프로젝트 루트에서 `pytest -v` 로 실행한다.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
