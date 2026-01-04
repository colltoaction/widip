import pytest
import asyncio
import io
import sys
from pathlib import Path
from computer.yaml import load
from computer.exec import titi_runner

@pytest.mark.parametrize("yaml_src, expected_substrings", [
    # 1. Accumulative Tap (Untagged sequence)
    ("!echo hello\n!echo world", ["hello\n", "world\n"]),
    # 2. Anchors and Aliases with explicit document separators
    ("&v !Data 42\n---\n*v", ["42\n"]),
    # 3. Mapping Fan-out
    ("key:\n  - !echo K\n  - !echo V", ["K\n", "V\n"]),
    # 4. Partial/Currying (if supported)
    # ("!echo:\n  - hello\n  - world", ["hello world\n"]),
])
def test_high_level_logic(yaml_src, expected_substrings):
    def _val_to_bytes(x):
        print(f"HOOK value_to_bytes: {x!r}", file=sys.stderr)
        if isinstance(x, bytes): return x
        return str(x).encode()

    hooks = {
        'stdout_write': lambda d: (print(f"HOOK stdout_write: {d!r}", file=sys.stderr), output.append(d.decode()))[1],
        'get_executable': lambda: "python3",
        'fspath': lambda x: x,
        'stdin_isatty': lambda: True,
        'set_recursion_limit': lambda n: None,
        'value_to_bytes': _val_to_bytes,
        'BytesIO': io.BytesIO,
        'Path': Path
    }
    output = []
    
    async def run_it():
        with titi_runner(hooks) as (runner, loop):
             diag = load(yaml_src)
             res = await runner(diag)
             # Mimic REPL print
             if res is not None:
                 if isinstance(res, tuple):
                     for r in res:
                        if hasattr(r, 'read'): r = await r.read()
                        hooks['stdout_write'](hooks['value_to_bytes'](r))
                 else:
                     if hasattr(res, 'read'): res = await res.read()
                     val = hooks['value_to_bytes'](res).decode()
                     if not val.endswith('\n'): val += '\n'
                     hooks['stdout_write'](val.encode())
             
    asyncio.run(run_it())
    combined = "".join(output)
    for expected in expected_substrings:
        assert expected in combined
