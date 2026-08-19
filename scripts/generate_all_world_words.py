"""Master script to generate all 7 world modules with 30 levels each (1,470 globally unique words)."""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Let's define the comprehensive vocabulary banks for Worlds 1 through 7.
