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
from .files import repl_read
from .computer import RECURSION_REGISTRY
from .thunk import unwrap, Thunk

T = TypeVar("T")

# --- Loop Management ---

LOOP_VAR: contextvars.ContextVar[asyncio.AbstractEventLoop | None] = contextvars.ContextVar("loop", default=None)

@contextmanager
def loop_scope(loop: asyncio.AbstractEventLoop | None = None):
    """Context manager for setting the asyncio loop in the current context.
    If no loop is provided, creates a new one (acting as an environment setup).
    """
    created = False
    if loop is None:
        sys.setrecursionlimit(10000)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        created = True
        if __debug__:
            import matplotlib
            matplotlib.use('agg')
    
    token = LOOP_VAR.set(loop)
    try:
        yield loop
    finally:
        LOOP_VAR.reset(token)
        if created:
            loop.close()

# --- Process Execution (Impure) ---

    def then(self, other: 'Process') -> 'Process':
        loop = self.loop or getattr(other, 'loop', None) or LOOP_VAR.get()
        
        async def _bridge_pipe(*args: T) -> Any:
            res = await unwrap(loop, self.inside(*args))
            if res is None: return res
            return await unwrap(loop, other.inside(*utils.tuplify(res)))

        return Process(_bridge_pipe, self.dom, other.cod, loop=loop)

    def tensor(self, other: 'Process') -> 'Process':
        loop = self.loop or getattr(other, 'loop', None) or LOOP_VAR.get()
        
        async def _tensor_inside(*args: T) -> tuple[Any, ...]:
            n = len(self.dom)
            args1, args2 = args[:n], args[n:]
            res1 = await unwrap(loop, self.inside(*args1))
            res2 = await unwrap(loop, other.inside(*args2))
            return utils.tuplify(res1) + utils.tuplify(res2)

        return Process(_tensor_inside, self.dom + other.dom, self.cod + other.cod, loop=loop)

    @classmethod
    def eval(cls, base: closed.Ty, exponent: closed.Ty, left: bool = True) -> 'Process':
        # Inlined evaluation logic to avoid LOOP_VAR reference
        async def _eval_func(f: Callable[..., Thunk[T]], *x: T) -> T:
             # Capture loop at call time via the Process call wrapper, 
             # but inside _eval_func we just need to unwrap.
             # Note: unwrap requires a loop.
             loop = LOOP_VAR.get() # Justified as we are in the impure execution context
             return await unwrap(loop, f(*x))
             
        return cls(_eval_func, (exponent << base) @ base, exponent)

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
    def __init__(self, stream: asyncio.StreamReader, process: asyncio.subprocess.Process):
        self.stream = stream
        self.process = process
    
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

async def _to_str(item: Any, loop: asyncio.AbstractEventLoop) -> str:
    res = await _to_bytes(item, loop)
    return res.decode()

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

    name_str = await _to_str(name, loop)
    args_str = [await _to_str(a, loop) for a in args]
    
    process = await asyncio.create_subprocess_exec(
        os.fspath(name_str), *args_str,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    async def feeder():
        try:
             in_stream = await unwrap(loop, stdin)
             if isinstance(in_stream, (list, tuple)):
                  for s in in_stream: await _pipe(s, process.stdin, loop)
             else:
                  await _pipe(in_stream, process.stdin, loop)
        except Exception:
             pass
        finally:
             if process.stdin.can_write_eof():
                  process.stdin.write_eof()
             process.stdin.close()

    async def _pipe(src, dest, l):
        if hasattr(src, 'read'):
             while True:
                  f = src.read(8192)
                  chunk = await f if asyncio.iscoroutine(f) else f
                  if not chunk: break
                  dest.write(chunk if isinstance(chunk, bytes) else chunk.encode())
                  await dest.drain()
        elif src is not None:
             v = await unwrap(l, src)
             if isinstance(v, bytes): d = v
             elif isinstance(v, str): d = v.encode()
             elif hasattr(v, 'read'):
                  r = v.read(); c = await r if asyncio.iscoroutine(r) else r
                  d = c if isinstance(c, bytes) else c.encode()
             else: d = str(v).encode()
             dest.write(d)
             await dest.drain()

    loop.create_task(feeder())
    return SubprocessStream(process.stdout, process)

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

async def read_shell(file_name: str, loop: asyncio.AbstractEventLoop) -> AsyncIterator[tuple[Any, Path | None, Any]]:
    """Yields parsed diagrams from the shell prompt. (Impure)"""
    while True:
        source_str = await shell_prompt(file_name, loop)
        if source_str is None: break
        if not source_str: 
             if not sys.stdin.isatty(): break
             continue
        yield repl_read(source_str), Path(file_name), BytesIO(b"")
        if not sys.stdin.isatty(): break

async def read_single(fd: Any, path: Path | None, args: list[str], loop: asyncio.AbstractEventLoop) -> AsyncIterator[tuple[Any, Path | None, Any]]:
    """Yields a single diagram from a file or command string. (Impure)"""
    input_stream = sys.stdin.buffer if not sys.stdin.isatty() else BytesIO(b"")
    yield fd, path, input_stream
