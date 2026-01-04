#!/usr/bin/env python3
"""
Monoidal Computer - Python Bootstrapping
"""
import sys
from pathlib import Path

def boot():
    print("\033[1;34m[System]\033[0m Booting Monoidal Computer (Python)...", file=sys.stderr)
    # Self-discovery
    v = sys.version_info
    print(f"\033[1;32m[Runtime]\033[0m Python {v.major}.{v.minor}.{v.micro}", file=sys.stderr)
    print("\033[1;34m[System]\033[0m Ready.", file=sys.stderr)

if __name__ == "__main__":
    boot()
