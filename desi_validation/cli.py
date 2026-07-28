from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .models import CandidateUpdate
from .validator import validate_candidate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a candidate state update with DESi.")
    parser.add_argument("input", nargs="?", help="JSON file; reads stdin when omitted")
    args = parser.parse_args(argv)

    try:
        raw = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
        candidate = CandidateUpdate.from_dict(json.loads(raw))
        result = validate_candidate(candidate)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
