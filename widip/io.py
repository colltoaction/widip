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


Int = symmetric.Ty("Int")

# --- Sync System Wrappers ---

@symmetric.Diagram.from_callable(Int, IO)
def set_recursion_limit(*args):
    return symmetric.Box("set_recursion_limit", Int, IO)(*args)


@symmetric.Diagram.from_callable(IO, Bool)
def stdin_isatty(*args) -> bool:
    return symmetric.Box("stdin_isatty", IO, Bool)(*args)


@symmetric.Diagram.from_callable(IO, Str)
def stdin_read(*args) -> str:
    return symmetric.Box("stdin_read", IO, Str)(*args)


@symmetric.Diagram.from_callable(Bytes, IO)
def stdout_write(*args):
    return symmetric.Box("stdout_write", Bytes, IO)(*args)


@symmetric.Diagram.from_callable(IO, Str)
def get_executable(*args) -> str:
    return symmetric.Box("get_executable", IO, Str)(*args)
