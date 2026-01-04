#!/usr/bin/env python3
"""
Recreates the make.py script.
"""
from pathlib import Path

def make():
    path = Path(__file__)
    content = path.read_text()
    path.write_text(content)
    path.chmod(0o755)
    print(f"Recreated {path.name}")

if __name__ == "__main__":
    make()
