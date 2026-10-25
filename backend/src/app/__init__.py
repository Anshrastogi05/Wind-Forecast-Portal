"""Compatibility layer: aliases windportal to app.*"""
from __future__ import annotations

import sys
import windportal as windportal

for name, mod in list(sys.modules.items()):
    if name.startswith("windportal"):
        sys.modules[name.replace("windportal", "app", 1)] = mod
