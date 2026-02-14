#!/usr/bin/env python3
"""
DEPRECATED: This script has been replaced by publish.py.

Use instead:
  python3 docs/scripts/publish.py agents   # Same functionality
  python3 docs/scripts/publish.py all      # Agents + Skills

This thin wrapper calls publish.py agents for backwards compatibility.
"""

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PUBLISH_SCRIPT = SCRIPT_DIR / "publish.py"


def main():
    print("⚠️  DEPRECATED: stitch-brain.py has been replaced by publish.py")
    print("   Run instead: python3 docs/scripts/publish.py agents")
    print()

    result = subprocess.run(
        [sys.executable, str(PUBLISH_SCRIPT), "agents"],
        cwd=SCRIPT_DIR.parent.parent,  # PROJECT_ROOT
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
