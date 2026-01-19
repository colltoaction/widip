import sys
from pathlib import Path
sys.path.append(str(Path.cwd() / "lib"))

from computer.yaml import load
from computer.core import Copy, Merge

def main():
    yaml_src = "key: value"
    diag = load(yaml_src)
    print(f"Boxes: {[b.name for b in diag.boxes]}")
    
    # Check if Copy and Merge are there
    names = [b.name for b in diag.boxes]
    print(f"Δ in names: {'Δ' in names}")
    print(f"μ in names: {'μ' in names}")

if __name__ == "__main__":
    main()
