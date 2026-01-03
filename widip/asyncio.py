"""Async operations and lazy evaluation (thunks) using asyncio."""
from collections.abc import Iterator, Callable, Awaitable, Sequence
from contextlib import contextmanager, ExitStack
from functools import partial
from typing import Any, TypeVar, Union, AsyncIterator
from pathlib import Path
import asyncio
import contextvars
import inspect

from discopy import closed, python, utils

T = TypeVar("T")
type EventLoop = asyncio.AbstractEventLoop
type AbstractEventLoop = asyncio.AbstractEventLoop


# Thunk is a zero-argument callable, an awaitable, or the value itself
type Thunk[T] = Union[Callable[[], Union[Awaitable[T], T]], Awaitable[T], T]

def thunk(f: Callable[..., Any], *args: Any) -> Callable[[], Any]:
    """Creates a thunk (lazy evaluation wrapper)."""
    return partial(f, *args)

def run(coro: Awaitable[T]) -> T:
    """Wrapper for asyncio.run."""
    return asyncio.run(coro)

# --- Event Loop Context ---

loop_var: contextvars.ContextVar[EventLoop | None] = contextvars.ContextVar("loop", default=None)

@contextmanager
def loop_scope(hooks: dict, loop: EventLoop | None = None):
    """Context manager for setting the event loop in the current context."""
    with ExitStack() as stack:
        created = False
        if loop is None:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                created = True
                stack.callback(loop.close)
        
        token = loop_var.set(loop)
        stack.callback(loop_var.reset, token)
        
        if created: 
             fn = hooks.get('set_recursion_limit')
             if fn: fn(10000)
        
        yield loop


# --- Memoization ---

Memo = dict[int, tuple[Any, asyncio.Future]]
memo_var: contextvars.ContextVar[Memo | None] = contextvars.ContextVar("memo", default=None)

@contextmanager
def recursion_scope():
    """Context manager for recursion memoization."""
    memo = memo_var.get()
    token = None
    if memo is None:
        memo = {}
        token = memo_var.set(memo)
    try:
        yield memo
    finally:
        if token:
            memo_var.reset(token)


# --- Unwrapping ---

async def callable_unwrap(func: Callable[[], Thunk[T]]) -> T:
    """Unwrap a callable thunk."""
    result = func()
    return await awaitable_unwrap(result)


async def awaitable_unwrap(aw: Thunk[T]) -> T:
    """Unwrap an awaitable until we get a concrete value."""
    while True:
        match aw:
            case _ if inspect.iscoroutine(aw) or inspect.isawaitable(aw):
                aw = await aw
            case _:
                return aw


async def unwrap_step(rec: Callable[[Any], Awaitable[T]], x: Thunk[T]) -> T | tuple[T, ...]:
    """Step function for recursive unwrapping."""
    while True:
        match x:
            case _ if callable(x) and not isinstance(x, (list, tuple, dict, str)):
                 x = await callable_unwrap(x)
            case _ if inspect.iscoroutine(x) or inspect.isawaitable(x):
                 x = await awaitable_unwrap(x)
            case _:
                 break

    if isinstance(x, (Iterator, tuple, list)):
        items = list(x)
        results = await asyncio.gather(*(rec(i) for i in items))
        return tuple(results)

    return x


async def recurse(
        f: Callable[..., Any],
        x: Any,
        loop: EventLoop,
        state: tuple[Memo, frozenset[int]] | None = None) -> Any:
    """Recursively apply a function with memoization."""
    if state is None:
         with recursion_scope() as memo:
             return await recurse(f, x, loop, (memo, frozenset()))

    memo, path = state
    id_x = id(x)
    
    if id_x in memo:
        _, fut = memo[id_x]
        if id_x in path:
            return x
        return await fut

    fut = loop.create_future()
    memo[id_x] = (x, fut)
    
    async def callback(item):
         return await recurse(f, item, loop, (memo, path | {id_x}))
         
    res = await callable_unwrap(lambda: f(callback, x))
    fut.set_result(res)
    return res


async def unwrap(loop: EventLoop, x: Thunk[T]) -> T | tuple[T, ...]:
    """Unwrap a thunk to its final value."""
    if loop is None:
         loop = loop_var.get() or asyncio.get_event_loop()
    return await recurse(unwrap_step, x, loop)


# --- Collection Operations ---

async def thunk_map(b: Iterator[Callable[[], Thunk[T]]]) -> tuple:
    """Map over thunks and gather results."""
    loop = asyncio.get_running_loop()
    coroutines = [unwrap(loop, kv()) for kv in b]
    results = await asyncio.gather(*coroutines)
    return sum(results, ())


async def thunk_reduce(b: Iterator[Callable[[], Thunk[T]]]) -> T:
    """Reduce thunks to a single value."""
    loop = asyncio.get_running_loop()
    res = None
    for f in b:
        res = f()
    return await unwrap(loop, res)


# --- Async Composition Helpers ---

async def pipe_async(left_fn, right_fn, loop, *args):
    """Compose two async functions sequentially (>>)."""
    res = await unwrap(loop, left_fn(*args))
    if res is None: 
        return res
    return await unwrap(loop, right_fn(*utils.tuplify(res)))


async def tensor_async(left_fn, left_dom, right_fn, loop, *args):
    """Compose two async functions in parallel (@)."""
    n = len(left_dom)
    args1, args2 = args[:n], args[n:]
    res1 = await unwrap(loop, left_fn(*args1))
    res2 = await unwrap(loop, right_fn(*args2))
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


async def read_subprocess_stream(stream: Any, process: asyncio.subprocess.Process, n: int = -1) -> bytes:
    """Read from subprocess stream and wait for process on EOF."""
    res = await stream.read(n)
    if not res:
         try:
             await process.wait()
         except Exception:
             pass
    return res


async def drain_stream(stream: Any):
    """Lazily read and yield chunks from a stream."""
    while True:
        chunk_coro = stream.read(8192)
        chunk = await chunk_coro if asyncio.iscoroutine(chunk_coro) else chunk_coro
        if not chunk:
            break
        yield chunk


# --- Stream Factories ---

def make_multi_stream_reader(streams: Iterator[Any], hooks: dict):
    """Create a multi-stream reader that lazily reads from multiple streams."""
    streams_list = list(streams)
    index = [0]
    
    class MultiStreamReader:
        def read(self, n: int = -1):
            return read_multi_stream(streams_list, index, hooks, n)
            
    return MultiStreamReader()


def make_subprocess_stream(stream: Any, process: asyncio.subprocess.Process, feeder_task: asyncio.Task | None = None):
    """Create a subprocess stream wrapper."""
    class SubprocessStream:
        def __init__(self, s, p, t):
            self.stream, self.process, self.feeder_task = s, p, t
        def read(self, n: int = -1):
            return read_subprocess_stream(self.stream, self.process, n)
            
    return SubprocessStream(stream, process, feeder_task)


# --- Subprocess and I/O Operations ---

async def to_bytes(item: Any, loop: EventLoop, hooks: dict) -> bytes:
    """Convert any value to bytes asynchronously."""
    val = await unwrap(loop, item)
    if isinstance(val, (list, tuple)):
        return b"".join([await to_bytes(i, loop, hooks) for i in val])
    return hooks['value_to_bytes'](val)


async def feed_stdin(loop: EventLoop, stdin: Any, process: asyncio.subprocess.Process, hooks: dict):
    """Feed data to subprocess stdin asynchronously."""
    try:
         in_stream = await unwrap(loop, stdin)
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
    from .computer import get_anchor, set_anchor
    
    # Check for recursive anchor
    item = get_anchor(name)
    if item is not None:
         if not callable(item):
              item = runner(item)
              set_anchor(name, item)
         return await unwrap(loop, item(stdin))

    # Execute subprocess
    name_str = (await to_bytes(name, loop, hooks)).decode()
    args_str = [(await to_bytes(a, loop, hooks)).decode() for a in args]
    
    process = await asyncio.create_subprocess_exec(
        hooks['fspath'](name_str), *args_str,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    task = loop.create_task(feed_stdin(loop, stdin, process, hooks))
    return make_subprocess_stream(process.stdout, process, task)


async def drain_to_stdout(stream: Any, hooks: dict):
    """Lazily read and print from a stream to stdout."""
    async for chunk in drain_stream(stream):
        hooks['stdout_write'](chunk)


async def printer(rec: Any, val: Any, hooks: dict):
    """Print output handler."""
    if hasattr(val, 'read'):
        await drain_to_stdout(val, hooks)
    elif isinstance(val, (list, tuple)):
        for item in val:
            if hasattr(item, 'read'):
                await drain_to_stdout(item, hooks)
            else:
                print(item)
    else:
        print(val)


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
    from .computer import interpreter
    return await interpreter(pipeline, source, loop, output_handler)


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
    with runner_ctx(hooks=hooks, executable=hooks['get_executable']()) as (runner, loop):
        params = get_params_fn(args.command_string, args.operands, hooks)
        source = read_fn(*params, loop, hooks)
        pipeline = make_pipeline_fn(runner)
        output_handler = partial(printer, hooks=hooks)

        if args.watch and args.operands:
            await eval_with_watch(pipeline, source, loop, output_handler, reload_fn)
        else:
            await eval_diagram(pipeline, source, loop, output_handler)
