import asyncio
import sys
import os
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Sequence
from io import BytesIO
from .files import repl_read
from .computer import RECURSION_REGISTRY
from .thunk import unwrap

# --- Stream Helpers ---

class MultiStreamReader:
    """Lazily reads from multiple streams sequentially without buffering to memory."""
    def __init__(self, streams):
        self._streams = list(streams)
        self._index = 0

    async def read(self, n: int = -1) -> bytes:
        while self._index < len(self._streams):
            stream = self._streams[self._index]
            # Handle potential thunks or awaitables in the stream list
            if not hasattr(stream, 'read'):
                # This shouldn't happen if run_merge is correct, but for safety:
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

# --- IO Handlers and Sources ---

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

async def read_single(fd: Any, path: Path | None, args: list[str], loop: asyncio.AbstractEventLoop) -> AsyncIterator[tuple[Any, Path | None, Any]]:
    """Source for a single execution from file or -c. (Impure)"""
    input_stream = sys.stdin.buffer if not sys.stdin.isatty() else BytesIO(b"")
    yield fd, path, input_stream

async def read_shell(file_name: str, loop: asyncio.AbstractEventLoop) -> AsyncIterator[tuple[Any, Path | None, Any]]:
    """Source for an interactive shell loop. (Impure)"""
    while True:
        try:
            if not sys.stdin.isatty():
                source_str = await loop.run_in_executor(None, sys.stdin.read)
                if not source_str: break
            else:
                prompt = f"--- !{file_name}\n"
                source_str = await loop.run_in_executor(None, input, prompt)
            
            yield repl_read(source_str), Path(file_name), BytesIO(b"")
            if not sys.stdin.isatty(): 
                break
        except EOFError:
            break
