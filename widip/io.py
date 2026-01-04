"""System I/O operations (stdin/stdout, files, no async)."""
import sys
import os
from typing import Any, TypeVar, Callable
from io import BytesIO
from pathlib import Path
from functools import singledispatch
from discopy import symmetric

T = TypeVar("T")

# --- Types ---
IO = symmetric.Ty("IO")
Bytes = symmetric.Ty("Bytes")
Str = symmetric.Ty("Str")
Bool = symmetric.Ty("Bool")
AnyTy = symmetric.Ty()

# --- Standard Input/Output ---

@symmetric.Diagram.from_callable(IO, Bytes)
def read_stdin(*args): 
    """Read from stdin if available, otherwise return empty BytesIO."""
    # args[0] is the input wire.
    def impl():
        if not sys.stdin.get('isatty', lambda: False)():
            return sys.stdin.buffer
        return BytesIO(b"")
    return symmetric.Box("read_stdin", IO, Bytes, data=impl)(*args)


@symmetric.Diagram.from_callable(AnyTy, Bytes)
def value_to_bytes(*args):
    """Convert a value to bytes (sync I/O operations)."""
    # AnyTy is empty, so args is empty.
    return symmetric.Box("value_to_bytes", AnyTy, Bytes)(*args)


# --- File and Diagram Parsing ---

@singledispatch
def _read_impl(source: Any, parser_fn) -> Any:
    """Default implementation: treat source as stream and parse."""
    return parser_fn(source)

_read_impl.register(str, lambda source, parser_fn: _read_impl(Path(source), parser_fn))
_read_impl.register(Path, lambda source, parser_fn: source.open().read())

Source = symmetric.Ty("Source")
Parser = symmetric.Ty("Parser")
Diagram = symmetric.Ty("Diagram")

@symmetric.Diagram.from_callable(Source @ Parser, Diagram)
def read_diagram_file(*args):
    """Parse a stream or file path using a parser function."""
    return symmetric.Box("read_diagram_file", Source @ Parser, Diagram)(*args)

# --- Hook Implementations (Native) ---

def impl_read_diagram_file(source: Any, parser_fn: Callable) -> Any:
    """Native implementation of diagram file reading."""
    if isinstance(source, str) and not os.path.exists(source):
        # Treat as raw string
        return parser_fn(source)
    path = Path(source)
    if path.exists():
        with open(path, 'r') as f:
            return parser_fn(f.read())
    return parser_fn(source)

def impl_get_executable(): return sys.executable
def impl_stdin_read(): return sys.stdin.read()
def impl_stdin_isatty(): return sys.stdin.isatty()
def impl_stdout_write(data): sys.stdout.buffer.write(data if isinstance(data, bytes) else data.encode())
def impl_set_recursion_limit(n): sys.setrecursionlimit(n)
