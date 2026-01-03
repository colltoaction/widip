from __future__ import annotations
import asyncio
import sys
import os
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Sequence, Generic, TypeVar
from io import BytesIO
from functools import partial
import contextvars
from contextlib import contextmanager

from discopy import closed, python, utils
from .files import repl_read, file_diagram
from .computer import RECURSION_REGISTRY
from .thunk import unwrap, Thunk

T = TypeVar("T")

# --- Loop Management ---

LOOP_VAR: contextvars.ContextVar[asyncio.AbstractEventLoop | None] = contextvars.ContextVar("loop", default=None)

@contextmanager
def loop_scope(loop: asyncio.AbstractEventLoop | None = None):
    """Context manager for setting the asyncio loop in the current context."""
    created = False
    if loop is None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            created = True
    
    token = LOOP_VAR.set(loop)
    try:
        if created: sys.setrecursionlimit(10000)
        yield loop
    finally:
        LOOP_VAR.reset(token)
        if created:
            loop.close()


# --- Process Execution (Impure) ---

    def then(self, other: 'Process') -> 'Process':
        loop = self.loop or getattr(other, 'loop', None) or LOOP_VAR.get()
        return Process(lambda *args: _bridge_pipe(self, other, loop, *args), self.dom, other.cod, loop=loop)

    def tensor(self, other: 'Process') -> 'Process':
        loop = self.loop or getattr(other, 'loop', None) or LOOP_VAR.get()
        return Process(lambda *args: _tensor_inside(self, other, loop, *args), self.dom + other.dom, self.cod + other.cod, loop=loop)

async def _bridge_pipe(self, other, loop, *args):
    res = await unwrap(loop, self.inside(*args))
    if res is None: return res
    return await unwrap(loop, other.inside(*utils.tuplify(res)))

async def _tensor_inside(self, other, loop, *args):
    n = len(self.dom)
    args1, args2 = args[:n], args[n:]
    res1 = await unwrap(loop, self.inside(*args1))
    res2 = await unwrap(loop, other.inside(*args2))
    return utils.tuplify(res1) + utils.tuplify(res2)

    @classmethod
    def eval(cls, base: closed.Ty, exponent: closed.Ty, left: bool = True) -> 'Process':
        return cls(lambda f, *x: unwrap(LOOP_VAR.get(), f(*x)), (exponent << base) @ base, exponent)

# --- Stream Helpers ---

class MultiStreamReader:
    """Lazily reads from multiple streams sequentially without buffering to memory."""
    def __init__(self, streams):
        self._streams = list(streams)
        self._index = 0

    async def read(self, n: int = -1) -> bytes:
        while self._index < len(self._streams):
            stream = self._streams[self._index]
            if not hasattr(stream, 'read'):
                val = str(stream).encode()
                self._streams[self._index] = BytesIO(val)
                stream = self._streams[self._index]

            res = stream.read(n)
            chunk = await res if asyncio.iscoroutine(res) else res
            if chunk:
                return chunk if isinstance(chunk, bytes) else chunk.encode()
            self._index += 1
        return b""

class SubprocessStream:
    """Wraps a StreamReader and keeps the process alive until EOF."""
    def __init__(self, stream: asyncio.StreamReader, process: asyncio.subprocess.Process, feeder_task: asyncio.Task | None = None):
        self.stream = stream
        self.process = process
        self.feeder_task = feeder_task
    
    async def read(self, n=-1):
        res = await self.stream.read(n)
        if not res:
             try:
                 await self.process.wait()
             except Exception:
                 pass
        return res

# --- Subprocess Logic ---

async def _to_bytes(item: Any, loop: asyncio.AbstractEventLoop) -> bytes:
    val = await unwrap(loop, item)
    if isinstance(val, (bytes, bytearray)): return bytes(val)
    if isinstance(val, str): return val.encode()
    if hasattr(val, 'read'):
        if hasattr(val, 'seek'): val.seek(0)
        res = val.read()
        if asyncio.iscoroutine(res): res = await res
        return res if isinstance(res, (bytes, bytearray)) else str(res).encode()
    if isinstance(val, (list, tuple)):
        return b"".join([await _to_bytes(i, loop) for i in val])
    return str(val).encode()

async def run_command(runner: Callable, loop: asyncio.AbstractEventLoop, name: Any, args: Sequence[Any], stdin: Any) -> Any:
    """Starts an async subprocess and returns its output stream."""
    if name in (registry := RECURSION_REGISTRY.get()):
         item = registry[name]
         if not callable(item):
              item = runner(item)
              new_registry = registry.copy()
              new_registry[name] = item
              RECURSION_REGISTRY.set(new_registry)
         return await unwrap(loop, item(stdin))

    name_str = (await _to_bytes(name, loop)).decode()
    args_str = [(await _to_bytes(a, loop)).decode() for a in args]
    
    process = await asyncio.create_subprocess_exec(
        os.fspath(name_str), *args_str,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    task = loop.create_task(_feed_stdin(loop, stdin, process))
    return SubprocessStream(process.stdout, process, task)

async def _feed_stdin(loop: asyncio.AbstractEventLoop, stdin: Any, process: asyncio.subprocess.Process):
    try:
         in_stream = await unwrap(loop, stdin)
         if __debug__: print(f"DEBUG: feeder input: {in_stream!r}", file=sys.stderr)
         
         items = in_stream if isinstance(in_stream, (list, tuple)) else (in_stream,)
         
         for src in items:
            if hasattr(src, 'read'):
                 while True:
                      f = src.read(8192)
                      chunk = await f if asyncio.iscoroutine(f) else f
                      if not chunk: break
                      process.stdin.write(chunk if isinstance(chunk, bytes) else chunk.encode())
                      await process.stdin.drain()
            elif src is not None:
                 v = await unwrap(loop, src)
                 if isinstance(v, bytes): d = v
                 elif isinstance(v, str): d = v.encode()
                 elif hasattr(v, 'read'):
                      r = v.read(); c = await r if asyncio.iscoroutine(r) else r
                      d = c if isinstance(c, bytes) else c.encode()
                 else: d = str(v).encode()
                 if __debug__: print(f"DEBUG: pipe writing: {d!r}", file=sys.stderr)
                 process.stdin.write(d)
                 await process.stdin.drain()

    except Exception as e:
         if __debug__: print(f"DEBUG: feeder error: {e}", file=sys.stderr)
    finally:
         if process.stdin.can_write_eof():
              process.stdin.write_eof()
         process.stdin.close()

# --- Output Handlers (Impure) ---

async def _drain_io(stream: Any):
    """Lazily read and print from a stream to stdout. (Impure)"""
    if hasattr(stream, 'read'):
        while True:
            res = stream.read(8192)
            chunk = await res if asyncio.iscoroutine(res) else res
            if not chunk: break
            data = chunk if isinstance(chunk, bytes) else chunk.encode()
            sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
    elif stream is not None:
        val = str(stream)
        if val: 
            sys.stdout.buffer.write(val.encode() + b"\n")
            sys.stdout.buffer.flush()

async def printer(rec: Callable, res: Any):
    """Output handler for the interpreter. (Impure)"""
    if isinstance(res, (list, tuple)):
         for i in res: 
             await printer(rec, i)
         return
    await _drain_io(res)

# --- Source Handlers (The "Read" role) ---

async def shell_prompt(file_name: str, loop: asyncio.AbstractEventLoop) -> str | None:
    """Prompt for input from stdin or tty. (Impure)"""
    try:
        if not sys.stdin.isatty():
             return sys.stdin.read()
        prompt = f"--- !{file_name}\n"
        return await loop.run_in_executor(None, input, prompt)
    except (EOFError, KeyboardInterrupt):
        return None
