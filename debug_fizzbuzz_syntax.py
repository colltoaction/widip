from widip.files import repl_read
from widip.compiler import SHELL_COMPILER
from widip.computer import Program, Data
from discopy import closed

yaml_str = """
- 1
- &loop
  ? !test {"{}", 15, "%"}
  : FizzBuzz
"""

try:
    d = repl_read(yaml_str)
    print(f"Diagram Type: {type(d)}")
    print(f"Diagram: {d}")
    
    # Let's see how the mapping key is compiled
    # d should be a Sequence of 2 items. The second item is the loop.
    loop = d.args[1]
    # loop is a Mapping (if it has keys)
    print(f"Loop Type: {type(loop)}")
    
    # Actually repl_read returns a Diagram.
    # I should look at the original YAML nodes if possible, but SHELL_COMPILER works on Yaml nodes (Scalar, Sequence, Mapping, etc.)
    # Wait, repl_read in widip/files.py converts incidences to diagram using SHELL_COMPILER?
    # No, it uses incidences_to_diagram.
    
    from widip.loader import load_sequence
    # I might need to mock the stream or use a higher level loader.
    
except Exception as e:
    import traceback
    traceback.print_exc()
