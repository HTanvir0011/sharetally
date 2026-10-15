"""Write the synthetic dataset to data/synthetic_dataset.json for inspection.

Usage:  python scripts/export_dataset.py
The app does not read this file; it regenerates the same data from the fixed seed.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sharetally.synthetic import build_dataset  # noqa: E402

if __name__ == "__main__":
    data = build_dataset()
    path = ROOT / "data" / "synthetic_dataset.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    counts = {k: len(v) for k, v in data.items() if isinstance(v, list)}
    print(f"wrote {path.relative_to(ROOT)}: {counts}")
