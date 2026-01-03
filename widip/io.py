"""System I/O operations (stdin/stdout, files, no async)."""
import sys
from typing import Any, TypeVar
from io import BytesIO

T = TypeVar("T")
type EventLoop = Any  # Event loop type without importing asyncio


# --- Standard Input/Output ---

def read_stdin():
    """Read from stdin if available, otherwise return empty BytesIO."""
    if not sys.stdin.isatty():
        return sys.stdin.buffer
    return BytesIO(b"")


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


# --- Sync System Wrappers ---

def set_recursion_limit(n: int):
    """Set the system recursion limit."""
    sys.setrecursionlimit(n)


def stdin_isatty() -> bool:
    """Check if stdin is a TTY."""
    return sys.stdin.isatty()


def stdin_read() -> str:
    """Read all from stdin."""
    return sys.stdin.read()


def stdout_write(data: bytes):
    """Write bytes to stdout buffer and flush."""
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()


def get_executable() -> str:
    """Get the current Python executable path."""
    return sys.executable
