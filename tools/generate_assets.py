#!/usr/bin/env python3
"""
DEPRECATED — use tools/generate_all_assets.py instead.

This file is kept for backward compatibility only.
All asset generation has been consolidated into generate_all_assets.py.
"""
from __future__ import annotations

import sys
import warnings

warnings.warn(
    "generate_assets.py is deprecated. Use generate_all_assets.py instead.",
    DeprecationWarning,
    stacklevel=2,
)

if __name__ == "__main__":
    from tools.generate_all_assets import main
    sys.exit(main())
