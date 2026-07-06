#!/usr/bin/env python3
"""Print ReqIQ onboarding checklist for a program manifest (PG-2)."""
from __future__ import annotations

import argparse
import json
import sys

from app.services.program_registry_service import build_reqiq_onboarding


def main() -> int:
    parser = argparse.ArgumentParser(description="ReqIQ onboarding checklist for a program")
    parser.add_argument("--manifest", required=True, help="Program slug (yaml stem)")
    args = parser.parse_args()
    data = build_reqiq_onboarding(args.manifest)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
