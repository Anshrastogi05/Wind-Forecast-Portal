import sys
from pathlib import Path

_backend_src = Path(__file__).resolve().parent / "backend" / "src"
if str(_backend_src) not in sys.path:
    sys.path.insert(0, str(_backend_src))
