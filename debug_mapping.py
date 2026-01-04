import sys
from pathlib import Path
sys.path.append(str(Path.cwd() / "lib"))

from computer.yaml import load, ren
from computer.core import Copy, Merge
import discopy

def main():
    yaml_src = "key: value"
    # Manual check of representation
    from computer.yaml.parse import impl_parse
    from computer.yaml import compose_functor
    
    rep = compose_functor(impl_parse(yaml_src))
    print(f"Rep classes: {[type(b) for b in rep.boxes]}")
    print(f"Rep names: {[b.name for b in rep.boxes]}")
    
    diag = load(yaml_src)
    print(f"Final boxes: {[b.name for b in diag.boxes]}")

if __name__ == "__main__":
    main()
