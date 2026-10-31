"""Generate frontend/src/data/generated/*.json from the canonical knowledge files.

    python scripts/sync_frontend_data.py          # write
    python scripts/sync_frontend_data.py --check  # exit 1 if generated files are stale (CI)

The phone number is only included when contact.show_phone is true in profile.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.knowledge import load_profile, load_projects, public_profile  # noqa: E402

KNOWLEDGE = BACKEND / "knowledge"
OUT = BACKEND.parent / "frontend" / "src" / "data" / "generated"


def render() -> dict[str, str]:
    profile = public_profile(load_profile(KNOWLEDGE)).model_dump(mode="json", exclude={"comment": True, "contact": {"note"}})
    projects = [p.model_dump(mode="json") for p in load_projects(KNOWLEDGE)]
    dump = lambda data: json.dumps(data, indent=2, ensure_ascii=False) + "\n"  # noqa: E731
    return {"profile.json": dump(profile), "projects.json": dump(projects)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files = render()
    OUT.mkdir(parents=True, exist_ok=True)
    stale = [n for n, c in files.items() if not (OUT / n).exists() or (OUT / n).read_text(encoding="utf-8") != c]
    if args.check:
        if stale:
            print(f"Stale generated data: {stale}. Run python scripts/sync_frontend_data.py", file=sys.stderr)
        return 1 if stale else 0
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8", newline="\n")
    print(f"Wrote {', '.join(files)} to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
