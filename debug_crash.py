import sys
import asyncio
from discopy import closed, monoidal, symmetric
from titi import computer, compiler, loader, yaml
from titi.exec import ExecFunctor

def test_crash():
    # Construct a simple diagram simulating test_complex_expr
    # !echo 1: !awk ...
    
    # Mapping structure
    # Copy(Node, 1) >> (Scalar(echo) >> Scalar(awk)) >> Merge(Node, 1)
    
    Node = symmetric.Ty("Node")
    echo = yaml.Scalar("!echo", "1", Node, Node)
    awk = yaml.Scalar("!awk", "...", Node, Node)
    
    # Inner diagram
    inner = echo >> awk
    
    # Mapping
    # Note: explicit construction to match loader
    con = loader.Copy(Node, 1)
    mer = loader.Merge(Node, 1)
    
    # Actually explicit mapping logic in loader uses this:
    # ob = to_symmetric(connector) >> tensor >> to_symmetric(merger)
    # tensor is inner
    diag = loader.to_symmetric(con) >> inner >> loader.to_symmetric(mer)
    
    print("Diagram constructed:", diag)
    
    # Compile
    print("Compiling...")
    compiled = compiler.SHELL_COMPILER(diag, compiler.SHELL_COMPILER, None)
    print("Compiled:", compiled)

if __name__ == "__main__":
    test_crash()
