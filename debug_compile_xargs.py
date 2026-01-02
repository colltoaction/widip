from widip.files import repl_read
from widip.compiler import SHELL_COMPILER
from widip.computer import Data, Copy, Swap, Discard
from discopy import closed

yaml_str = "!xargs { test, -eq, 0 }"

try:
    d = repl_read(yaml_str)
    print(f"Diagram: {d}")
    compiled = SHELL_COMPILER(d)
    print(f"Compiled: {compiled}")
    
    # Let's inspect the boxes of the inner diagram of the compiled mapping
    # Assuming d is a Mapping
    inner_diag = SHELL_COMPILER(d.args[0])
    print(f"Inner boxes: {inner_diag.boxes}")
    for i, box in enumerate(inner_diag.boxes):
        print(f"Box {i}: {box}, type: {type(box)}")
        print(f"Is instance of Data: {isinstance(box, Data)}")
        print(f"Is instance of Copy: {isinstance(box, Copy)}")

except Exception as e:
    import traceback
    traceback.print_exc()
