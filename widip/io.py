"""System I/O operations (stdin/stdout, files, no async)."""
import sys
import os
from pathlib import Path
from typing import Any, Callable, Sequence, TypeVar
from io import BytesIO
import contextvars
from contextlib import contextmanager

from discopy import closed, python

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


# --- Event Loop Context ---

LOOP_VAR: contextvars.ContextVar[EventLoop | None] = contextvars.ContextVar("loop", default=None)

@contextmanager
def loop_scope(loop: EventLoop | None = None):
    """Context manager for setting the event loop in the current context."""
    import asyncio as aio
    from contextlib import ExitStack
    
    with ExitStack() as stack:
        created = False
        if loop is None:
            try:
                loop = aio.get_running_loop()
            except RuntimeError:
                loop = aio.new_event_loop()
                aio.set_event_loop(loop)
                created = True
                stack.callback(loop.close)
        
        token = LOOP_VAR.set(loop)
        stack.callback(LOOP_VAR.reset, token)
        
        if created: 
            sys.setrecursionlimit(10000)
        
        yield loop


# --- Type Alias ---

Thunk = Any  # Re-export for compatibility
