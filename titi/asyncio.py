"""Async operations and lazy evaluation (thunks) using asyncio."""
from collections.abc import Iterator, Callable, Awaitable, Sequence, AsyncIterator
from functools import partial
from typing import Any, TypeVar, Union, AsyncIterator
from pathlib import Path
import asyncio
import contextvars
import inspect
import sys

from discopy import closed, python, utils

T = TypeVar("T")
EventLoop = asyncio.AbstractEventLoop
AbstractEventLoop = asyncio.AbstractEventLoop


# --- Event Loop Context ---

loop_var: contextvars.ContextVar[EventLoop | None] = contextvars.ContextVar("loop", default=None)

def run(coro):
    """Run a coroutine to completion."""
    return asyncio.run(coro)

class loop_scope:
    """Class-based context manager for setting the event loop."""
    def __init__(self, hooks: dict, loop: EventLoop | None = None):
        self.hooks = hooks
        self.loop = loop
        self.created = False
        self.token = None

    def __enter__(self):
        if self.loop is None:
            try:
                self.loop = asyncio.get_running_loop()
            except RuntimeError:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
                self.created = True
        
        self.token = loop_var.set(self.loop)
        
        if self.created: 
             fn = self.hooks.get('set_recursion_limit')
             if fn: fn(10000)
        return self.loop

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            try:
                loop_var.reset(self.token)
            except ValueError: pass # Different context
        if self.created:
            self.loop.close()


# --- Unwrapping ---

async def callable_unwrap(func: Callable[[], Any], loop: EventLoop, memo: dict) -> Any:
    """Unwrap a callable."""
    result = func()
    return await awaitable_unwrap(result, loop, memo)


async def awaitable_unwrap(aw: Any, loop: EventLoop, memo: dict) -> Any:
    """Unwrap an awaitable until we get a concrete value."""
    while True:
        match aw:
            case _ if inspect.iscoroutine(aw) or inspect.isawaitable(aw):
                aw = await aw
            case _:
                return aw


async def unwrap_step(rec: Callable[[Any], Awaitable[T]], x: Any, loop: EventLoop, memo: dict) -> T | tuple[T, ...]:
    """Step function for recursive unwrapping."""
    while True:
        match x:
            case _ if callable(x) and not isinstance(x, (list, tuple, dict, str, bytes)):
                 x = await rec(await x() if inspect.iscoroutinefunction(x) else x())
            case _ if inspect.iscoroutine(x) or inspect.isawaitable(x):
                 x = await x
            case _:
                 break

    if isinstance(x, (Iterator, tuple, list)) and not isinstance(x, (str, bytes)):
        items = list(x)
        results = await asyncio.gather(*(rec(i) for i in items))
        return tuple(results)

    return x


async def recurse(
        f: Callable[..., Any],
        x: Any,
        loop: EventLoop,
        memo: dict,
        path: frozenset[int] = frozenset()) -> Any:
    """Recursively apply a function with memoization."""
    id_x = id(x)
    if id_x in memo:
        _, fut = memo[id_x]
        if id_x in path: return x
        return await fut

    fut = loop.create_future()
    memo[id_x] = (x, fut)
    
    async def callback(item):
         return await recurse(f, item, loop, memo, path | {id_x})
         
    res = await f(callback, x, loop, memo)
    fut.set_result(res)
    return res


async def unwrap(x: Any, loop: EventLoop, memo: dict | None = None) -> Any:
    """Unwrap a lazy value to its final value."""
    if x is None: return None
    if memo is None: memo = {}
    return await recurse(unwrap_step, x, loop, memo)


# --- Async Composition Helpers ---

async def pipe_async(left_fn, right_fn, loop, *args):
    """Compose two async functions sequentially (>>)."""
    res = await unwrap(left_fn(*args), loop)
    if res is None: 
        return res
    return await unwrap(right_fn(*utils.tuplify(res)), loop)


async def tensor_async(left_fn, left_dom, right_fn, loop, *args):
    """Compose two async functions in parallel (@)."""
    n = len(left_dom)
    args1, args2 = args[:n], args[n:]
    res1 = await unwrap(left_fn(*args1), loop)
    res2 = await unwrap(right_fn(*args2), loop)
    return utils.tuplify(res1) + utils.tuplify(res2)


# --- Async Stream Operations ---

async def read_multi_stream(streams_list: list, index: list[int], hooks: dict, n: int = -1) -> bytes:
    """Read from multiple streams sequentially."""
    BytesIO = hooks['BytesIO']
    while index[0] < len(streams_list):
        stream = streams_list[index[0]]
        if not hasattr(stream, 'read'):
            val = hooks['value_to_bytes'](stream)
            streams_list[index[0]] = BytesIO(val)
            stream = streams_list[index[0]]

        res = stream.read(n)
        chunk = await res if asyncio.iscoroutine(res) else res
        if chunk:
            return chunk if isinstance(chunk, bytes) else chunk.encode()
        index[0] += 1
    return b""


async def to_bytes(item: Any, loop: EventLoop, hooks: dict) -> bytes:
    """Convert any value to bytes asynchronously."""
    val = await unwrap(item, loop)
    if val is None: return b""
    if isinstance(val, bytes): return val
    if isinstance(val, (str, int, float, bool)): return str(val).encode()
    if isinstance(val, (list, tuple)):
        return b"".join([await to_bytes(i, loop, hooks) for i in val])
    if hasattr(val, 'read'):
        res = val.read()
        chunk = await res if asyncio.iscoroutine(res) else res
        return chunk if isinstance(chunk, bytes) else str(chunk).encode()
    return hooks['value_to_bytes'](val)

async def unwrap_to_str(item: Any, loop: EventLoop, hooks: dict) -> str:
    """Unwrap a value and return it as a string."""
    res = await to_bytes(item, loop, hooks)
    return res.decode()

async def drain_stream(stream: Any):
    """Lazily read and yield chunks from a stream."""
    while True:
        try:
            chunk_coro = stream.read(8192)
            chunk = await chunk_coro if asyncio.iscoroutine(chunk_coro) else chunk_coro
            if not chunk: break
            yield chunk
        except Exception: break


async def feed_stdin(loop: EventLoop, stdin: Any, process: asyncio.subprocess.Process, hooks: dict):
    """Feed data to subprocess stdin asynchronously."""
    try:
         in_stream = await unwrap(stdin, loop)
         if in_stream is None: return
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
                 v = await unwrap(src, loop)
                 if v is None: continue
                 if isinstance(v, bytes): 
                     d = v
                 elif isinstance(v, str): 
                     d = v.encode()
                 elif hasattr(v, 'read'):
                      r = v.read()
                      c = await r if asyncio.iscoroutine(r) else r
                      d = c if isinstance(c, bytes) else c.encode()
                 else: 
                     d = str(v).encode()
                 process.stdin.write(d)
                 await process.stdin.drain()
    except Exception:
         pass
    finally:
         try:
              if process.stdin.can_write_eof():
                   process.stdin.write_eof()
              process.stdin.close()
         except Exception:
              pass


async def run_command(runner: Callable, loop: EventLoop, 
                     name: Any, args: Sequence[Any], stdin: Any, hooks: dict) -> Any:
    """Starts an async subprocess and returns its output stream."""
    from computer import get_anchor, set_anchor
    
    # 1. Recursive anchor check
    name_str = await unwrap_to_str(name, loop, hooks)
    item = get_anchor(name_str)
    if item is not None:
         if not callable(item):
              item = runner(item)
              set_anchor(name_str, item)
         return await unwrap(item(stdin), loop)

    # 2. Execute subprocess
    args_str = [await unwrap_to_str(a, loop, hooks) for a in args]
    
    # xargs as a GUARD (Special Case)
    if name_str == "xargs":
         process = await asyncio.create_subprocess_exec(
             hooks['fspath'](name_str), *args_str,
             stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
         )
         await feed_stdin(loop, stdin, process, hooks)
         stdout_data, _ = await process.communicate()
         return None if process.returncode != 0 else (stdout_data if stdout_data.strip() else stdin)

    process = await asyncio.create_subprocess_exec(
        hooks['fspath'](name_str), *args_str,
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=None
    )
    
    # Fire-and-forget stdin feeder
    loop.create_task(feed_stdin(loop, stdin, process, hooks))
    
    # Attach a simple 'waiter' to the stream so it cleans up the process on EOF
    original_read = process.stdout.read
    async def wrapped_read(n=-1):
        res = await original_read(n)
        if not res: 
             try: await process.wait()
             except: pass
        return res
    process.stdout.read = wrapped_read
    
    return process.stdout


async def drain_to_stdout(stream: Any, hooks: dict):
    """Lazily read and print from a stream to stdout."""
    async for chunk in drain_stream(stream):
        hooks['stdout_write'](chunk)


async def printer(rec: Any, val: Any, hooks: dict):
    """Print output handler."""
    if val is None: return
    if hasattr(val, 'read'):
        await drain_to_stdout(val, hooks)
    elif isinstance(val, bytes):
        hooks['stdout_write'](val)
    elif isinstance(val, (list, tuple)):
        for item in val:
            if item is None: continue
            if hasattr(item, 'read'):
                await drain_to_stdout(item, hooks)
            elif isinstance(item, bytes):
                hooks['stdout_write'](item)
            else:
                hooks['stdout_write'](str(item).encode() + b"\n")
    else:
        hooks['stdout_write'](str(val).encode() + b"\n")


async def run_with_watcher(coro, reload_fn):
    """Run a coroutine with file watching enabled."""
    try:
        from watchfiles import awatch
    except ImportError:
        await coro
        return

    async def watch_task():
        async for changes in awatch('.', watch_filter=lambda _, path: path.endswith('.yaml')):
            for change_type, path in changes:
                reload_fn(path)

    async def main_task():
        await coro

    watch = asyncio.create_task(watch_task())
    main = asyncio.create_task(main_task())
    
    try:
        await main
    finally:
        watch.cancel()


# --- Async REPL Logic ---

async def prompt_loop(file_name: str, loop: EventLoop, hooks: dict) -> AsyncIterator[str]:
    """Interactive prompt loop for REPL mode."""
    while True:
        try:
            if not hooks['stdin_isatty']():
                 source_str = hooks['stdin_read']()
            else:
                 prompt = f"--- !{file_name}\n"
                 source_str = await loop.run_in_executor(None, input, prompt)
        except (EOFError, KeyboardInterrupt):
            break

        if not source_str: 
             if not hooks['stdin_isatty'](): break
             continue
        yield source_str
        if not hooks['stdin_isatty'](): break


async def async_read(fd: Any | None, path: Path | None, file_name: str, loop: EventLoop, 
                     parse_fn: Callable[[str], Any], read_stdin_fn: Callable[[], Any], hooks: dict) -> AsyncIterator[tuple[Any, Path | None, Any]]:
    """Yields parsed diagrams from a file, command string, or shell prompt."""
    if fd is not None:
         input_stream = read_stdin_fn()
         yield fd, path, input_stream
         return

    async for source_str in prompt_loop(file_name, loop, hooks):
        BytesIO = hooks['BytesIO']
        Path_type = hooks['Path']
        yield parse_fn(source_str), Path_type(file_name), BytesIO(b"")


async def eval_diagram(pipeline: Callable, source: AsyncIterator, loop: EventLoop, output_handler: Callable):
    """Evaluate diagrams through the pipeline."""
    async for diagram, path, stdin in source:
        result = await pipeline(diagram, stdin)
        await output_handler(None, result)


async def eval_with_watch(pipeline: Callable, source: AsyncIterator, loop: EventLoop, 
                          output_handler: Callable, reload_fn: Callable):
    """Evaluate with file watching enabled."""
    await run_with_watcher(
        eval_diagram(pipeline, source, loop, output_handler),
        reload_fn=reload_fn
    )


async def run_repl(env_fn: Callable, runner_ctx: Callable, get_params_fn: Callable, read_fn: Callable,
                   make_pipeline_fn: Callable, reload_fn: Callable, hooks: dict):
    """Orchestrate the async REPL execution."""
    args = env_fn()
    with runner_ctx(hooks=hooks, executable=hooks['get_executable']()) as runner_data:
        runner_fn, loop = runner_data
        params = get_params_fn(args.command_string, args.operands, hooks)
        source = read_fn(*params, loop, hooks)
        pipeline = make_pipeline_fn(runner_data)
        output_handler = partial(printer, hooks=hooks)

        if args.watch and args.operands:
            await eval_with_watch(pipeline, source, loop, output_handler, reload_fn)
        else:
            await eval_diagram(pipeline, source, loop, output_handler)
