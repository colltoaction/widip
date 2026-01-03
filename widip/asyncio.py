"""Async operations and lazy evaluation (thunks)."""
from collections.abc import Iterator, Callable, Awaitable
from contextlib import contextmanager
from functools import partial
from typing import Any, TypeVar, Union
import asyncio
import contextvars
import inspect

T = TypeVar("T")
type EventLoop = asyncio.AbstractEventLoop

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


# --- Thunk Type and Operations ---

# Thunk is a zero-argument callable, an awaitable, or the value itself
Thunk = Union[Callable[[], Union[Awaitable[T], T]], Awaitable[T], T]

def thunk(f: Callable[..., T], *args: Any) -> Callable[[], T]:
    """Creates a thunk (lazy evaluation wrapper)."""
    return partial(f, *args)


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
    from discopy import utils
    res = await unwrap(loop, left_fn(*args))
    if res is None: 
        return res
    return await unwrap(loop, right_fn(*utils.tuplify(res)))


async def tensor_async(left_fn, left_dom, right_fn, loop, *args):
    """Compose two async functions in parallel (@)."""
    from discopy import utils
    n = len(left_dom)
    args1, args2 = args[:n], args[n:]
    res1 = await unwrap(loop, left_fn(*args1))
    res2 = await unwrap(loop, right_fn(*args2))
    return utils.tuplify(res1) + utils.tuplify(res2)


# --- Process Wrapper ---

class Process:
    """Wraps an async function with loop context awareness."""
    def __init__(self, inside: Callable, dom, cod, loop: EventLoop | None = None):
        self.inside = inside
        self.dom = dom
        self.cod = cod
        self.loop = loop
        self.name = getattr(inside, '__name__', 'Process')

    def then(self, other: 'Process') -> 'Process':
        from .io import LOOP_VAR
        loop = self.loop or getattr(other, 'loop', None) or LOOP_VAR.get()
        return Process(lambda *args: pipe_async(self.inside, other.inside, loop, *args), 
                      self.dom, other.cod, loop=loop)

    def tensor(self, other: 'Process') -> 'Process':
        from .io import LOOP_VAR
        loop = self.loop or getattr(other, 'loop', None) or LOOP_VAR.get()
        return Process(lambda *args: tensor_async(self.inside, self.dom, other.inside, loop, *args), 
                      self.dom + other.dom, self.cod + other.cod, loop=loop)

    def __call__(self, *args):
        return self.inside(*args)
    
    # DisCoPy Category interface
    @classmethod
    def id(cls, dom):
        """Identity morphism."""
        return cls(lambda *x: x[0] if len(x) == 1 else x, dom, dom)
    
    def __rshift__(self, other):
        """Sequential composition (>>)."""
        return self.then(other)
    
    def __matmul__(self, other):
        """Parallel composition (@)."""
        return self.tensor(other)

    @classmethod
    def eval(cls, base, exponent, left: bool = True) -> 'Process':
        from .io import LOOP_VAR
        return cls(lambda f, *x: unwrap(LOOP_VAR.get(), f(*x)), 
                  (exponent << base) @ base, exponent)


# --- Async Stream Operations ---

async def read_multi_stream(streams_list, index, n: int = -1) -> bytes:
    """Read from multiple streams sequentially."""
    from io import BytesIO
    while index[0] < len(streams_list):
        stream = streams_list[index[0]]
        if not hasattr(stream, 'read'):
            val = str(stream).encode()
            streams_list[index[0]] = BytesIO(val)
            stream = streams_list[index[0]]

        res = stream.read(n)
        chunk = await res if asyncio.iscoroutine(res) else res
        if chunk:
            return chunk if isinstance(chunk, bytes) else chunk.encode()
        index[0] += 1
    return b""


async def read_subprocess_stream(stream, process, n=-1) -> bytes:
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


# --- Subprocess and I/O Operations ---

async def to_bytes(item: Any, loop: EventLoop) -> bytes:
    """Convert any value to bytes asynchronously."""
    from .io import value_to_bytes
    val = await unwrap(loop, item)
    if isinstance(val, (list, tuple)):
        return b"".join([await to_bytes(i, loop) for i in val])
    return value_to_bytes(val)


async def feed_stdin(loop: EventLoop, stdin: Any, process):
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
         if process.stdin.can_write_eof():
              process.stdin.write_eof()
         process.stdin.close()


async def run_command(runner: Callable, loop: EventLoop, 
                     name: Any, args, stdin: Any) -> Any:
    """Starts an async subprocess and returns its output stream."""
    import os
    from .computer import get_anchor, set_anchor
    from .io import make_subprocess_stream
    
    # Check for recursive anchor
    item = get_anchor(name)
    if item is not None:
         if not callable(item):
              item = runner(item)
              set_anchor(name, item)
         return await unwrap(loop, item(stdin))

    # Execute subprocess
    name_str = (await to_bytes(name, loop)).decode()
    args_str = [(await to_bytes(a, loop)).decode() for a in args]
    
    process = await asyncio.create_subprocess_exec(
        os.fspath(name_str), *args_str,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    task = loop.create_task(feed_stdin(loop, stdin, process))
    return make_subprocess_stream(process.stdout, process, task)


async def drain_to_stdout(stream: Any):
    """Lazily read and print from a stream to stdout."""
    import sys
    async for chunk in drain_stream(stream):
        sys.stdout.buffer.write(chunk)
        sys.stdout.buffer.flush()


async def printer(rec: Any, val: Any):
    """Print output handler."""
    if hasattr(val, 'read'):
        await drain_to_stdout(val)
    elif isinstance(val, (list, tuple)):
        for item in val:
            if hasattr(item, 'read'):
                await drain_to_stdout(item)
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

