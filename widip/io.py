"""System I/O operations (stdin/stdout, files, no async)."""
import sys
from typing import Any, TypeVar
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
def read_stdin():
    """Read from stdin if available, otherwise return empty BytesIO."""
    if not sys.stdin.isatty():
        return sys.stdin.buffer
    return BytesIO(b"")


@symmetric.Diagram.from_callable(AnyTy, Bytes)
def value_to_bytes(val: Any) -> bytes:
    """Convert a value to bytes (sync I/O operations)."""
    if isinstance(val, (bytes, bytearray)): 
        return bytes(val)
    if isinstance(val, str): 
        return val.encode()
    if hasattr(val, 'read'):
        if hasattr(val, 'seek'): 
            val.seek(0)
        res = val.read()
        return res if isinstance(res, (bytes, bytearray)) else str(res).encode()
    return str(val).encode()


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
def read_diagram_file(source: Any, parser_fn) -> Any:
    """Parse a stream or file path using a parser function."""
    return _read_impl(source, parser_fn)


Int = symmetric.Ty("Int")

# --- Sync System Wrappers ---

@symmetric.Diagram.from_callable(Int, IO)
def set_recursion_limit(n: int):
    sys.setrecursionlimit(n)


@symmetric.Diagram.from_callable(IO, Bool)
def stdin_isatty() -> bool:
    return sys.stdin.isatty()


@symmetric.Diagram.from_callable(IO, Str)
def stdin_read() -> str:
    return sys.stdin.read()


@symmetric.Diagram.from_callable(Bytes, IO)
def stdout_write(data: bytes):
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()


@symmetric.Diagram.from_callable(IO, Str)
def get_executable() -> str:
    return sys.executable
