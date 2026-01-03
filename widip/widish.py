import asyncio
from functools import partial
from typing import Any, Awaitable, Callable, Sequence, IO
from io import StringIO
from discopy.utils import tuplify, untuplify
from discopy import closed, python, utils

from .computer import *
from .thunk import unwrap

async def _bridge_pipe(f: Callable[..., Awaitable[Any]], g: Callable[..., Awaitable[Any]], *args: Any) -> Any:
    res = await unwrap(f(*args))
    
    def is_failure(x: Any) -> bool:
        if x is None: return True
        return False

    if is_failure(res):
        return res
    
    return await unwrap(g(*utils.tuplify(res)))

async def _tensor_inside(f: Callable[..., Awaitable[Any]], g: Callable[..., Awaitable[Any]], n: int, *args: Any) -> Any:
    args1, args2 = args[:n], args[n:]
    res1 = await unwrap(f(*args1))
    res2 = await unwrap(g(*args2))
    return tuplify(res1) + tuplify(res2)

async def _eval_func(f: Callable[..., Awaitable[Any]], *x: Any) -> Any:
    return await unwrap(f(*x))

def _lazy(func: Callable[..., Awaitable[Any]], ar: Any) -> Callable[..., Awaitable[Any]]:
    """Returns a function that returns a partial application of func."""
    async def wrapper(*args: Any) -> Any:
        return partial(func, ar, *args)
    return wrapper

class Process(python.Function):
    def __init__(self, inside: Callable[..., Awaitable[Any]], dom: Any, cod: Any):
        super().__init__(inside, dom, cod)
        self.type_checking = False

    async def __call__(self, *args: Any) -> Any:
        # We need to unwrap the result of the internal function
        ar = getattr(self, "ar", None)
        res = await unwrap(self.inside(*args))
        
        # Feedback trace: print results of all atomic boxes
        if ar and isinstance(ar, (Data, Eval, Program)):
             from .interactive import flatten
             # Flatten reads streams if necessary? 
             # For now, assume flatten handles generic objects or we skip trace for simplicity during refactor
             pass
        return res

    def then(self, other: 'Process') -> 'Process':
        return Process(
            partial(_bridge_pipe, self, other),
            self.dom,
            other.cod,
        )

    def tensor(self, other: 'Process') -> 'Process':
        return Process(
            partial(_tensor_inside, self, other, len(self.dom)),
            self.dom + other.dom,
            self.cod + other.cod
        )

    @classmethod
    def eval(cls, base: Any, exponent: Any, left: bool = True) -> 'Process':
        return Process(
            _eval_func,
            (exponent << base) @ base,
            exponent
        )

    @staticmethod
    def split_args(ar: Any, *args: Any) -> tuple[tuple[Any, ...], tuple[Any, ...]]:
        try:
            n = len(ar.dom)
        except TypeError:
            n = 1
        return args[:n], args[n:]

    @staticmethod
    async def run_constant(ar: Any, *args: Any) -> tuple[Any, ...]:
        if ar.value:
            return (StringIO(ar.value), )
        n = 1
        return args[n:] if len(args) > n else ()

    @staticmethod
    async def run_map(ar: Any, *args: Any) -> tuple[Any, ...]:
        runner = SHELL_RUNNER(ar.args[0])
        res = await runner(*args)
        return tuple(tuplify(res))

    @staticmethod
    async def run_seq(ar: Any, *args: Any) -> Any:
        runner = SHELL_RUNNER(ar.args[0])
        return await runner(*args)

    @staticmethod
    def run_swap(ar: Any, *args: Any) -> tuple[Any, ...]:
        n_left = len(ar.left)
        n_right = len(ar.right)
        left_args = args[:n_left]
        right_args = args[n_left : n_left + n_right]
        return untuplify(right_args + left_args)

    @staticmethod
    def run_cast(ar: Any, *args: Any) -> Any:
        return args[0] if args else None

    @staticmethod
    def run_copy(ar: Any, *args: Any) -> tuple[Any, ...]:
        val = args[0] if args else None
        if val is None:
             return (None,) * ar.n
        
        # If val is IO stream, read and replicate
        if hasattr(val, 'read'):
             data = val.read()
             return tuple(StringIO(data) for _ in range(ar.n))
        return (val,) * ar.n

    @staticmethod
    def run_discard(ar: Any, *args: Any) -> tuple[Any, ...]:
        # Consume stream to avoid leaks/buffering issues?
        for arg in args:
             if hasattr(arg, 'read'): arg.read()
        return ()

    @staticmethod
    def run_merge(ar: Any, *args: Any) -> tuple[Any, ...]:
        # Merge streams into one
        contents = []
        for arg in args:
             if hasattr(arg, 'read'):
                 contents.append(arg.read())
             else:
                 contents.append(str(arg) if arg is not None else "")
        return (StringIO("".join(contents)),)

    @staticmethod
    async def _exec_subprocess(name: str, args: tuple[str, ...], stdin: IO[str]) -> IO[str]:
        process: asyncio.subprocess.Process = await asyncio.create_subprocess_exec(
            name, *args,
            stdout=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        # Read from input stream
        content = stdin.read()
        input_data: bytes | None = content.encode() if content else None
        
        stdout_data: bytes | None
        stderr_data: bytes | None
        stdout_data, stderr_data = await process.communicate(input=input_data)
        
        if process.returncode != 0:
             return StringIO("") # or failure indication? For now empty stream

        if stdout_data is None:
             return StringIO("")

        return StringIO(stdout_data.decode())

    @staticmethod
    async def run_command(name: Any, args: Any, stdin: IO[str]) -> IO[str]:
        from .widish import SHELL_RUNNER
        from .compiler import SHELL_COMPILER
        
        # stdin is a single stream now
        
        if not isinstance(name, str):
             # Name is a box? Eval case for name?
             # For simplicity, assume name is string for command execution
             return StringIO("")

        if name in (registry := RECURSION_REGISTRY.get()):
             item = registry[name]
             if not callable(item):
                  compiled = SHELL_COMPILER(item)
                  runner = SHELL_RUNNER(compiled)
                  registry[name] = runner
                  RECURSION_REGISTRY.set(dict(registry))
             else:
                  runner = item
             # Pass stdin stream as argument
             return await runner(stdin)

        if name.endswith(".yaml"):
            str_args = tuple(map(str, args))
            args = (name, ) + str_args
            name = "bin/widish"
            
        str_args = tuple(map(str, args))
        return await Process._exec_subprocess(name, str_args, stdin)

    @staticmethod
    async def deferred_exec(ar: Any, *args: Any) -> Any:
        async def resolve(x: Any) -> Any:
            if callable(x):
                return await unwrap(x())
            return x

        resolved = []
        for x in args:
            res = await resolve(x)
            resolved.append(res)
        
        if ar.name:
             name = ar.name
             cmd_args = resolved
             stdin_wires = []
        else:
             if not resolved: return StringIO("")
             name = resolved[0]
             # Eval wrapping name? If name is stream, read it.
             if hasattr(name, 'read'): name = name.read().strip()
             
             stdin_wires = resolved[-1]
             # If stdin_wires is list (from multiple wires), flattening needed?
             # Resolved[-1] is usually tuple from previous box
             if isinstance(stdin_wires, (tuple, list)):
                  pass 
             else:
                   stdin_wires = [stdin_wires]
                   
             cmd_args = resolved[1:-1]

        # Unwrap arguments (if streams, read them?)
        # Arguments to command are usually strings.
        final_args = []
        for arg in cmd_args:
             if isinstance(arg, (tuple, list)):
                  arg = arg[0] if arg else ""
             if hasattr(arg, 'read'):
                  final_args.append(arg.read().strip())
             else:
                  final_args.append(str(arg))
             
        # Prepare Stdin Stream
        # Concat multiple input streams
        stdin_contents = []
        if isinstance(stdin_wires, (tuple, list)):
             for w in stdin_wires:
                  if hasattr(w, 'read'): stdin_contents.append(w.read())
                  else: stdin_contents.append(str(w) if w else "")
        else:
              if hasattr(stdin_wires, 'read'): stdin_contents.append(stdin_wires.read())
              else: stdin_contents.append(str(stdin_wires) if stdin_wires else "")
              
        stdin_stream = StringIO("".join(stdin_contents))

        return await Process.run_command(name, final_args, stdin_stream)

    @staticmethod
    async def run_program(ar: Any, *args: Any) -> Any:
        # Programs take all inputs from wires as stdin
        return await Process.run_command(ar.name, ar.args, args)

    @staticmethod
    def run_constant_gamma(ar: Any, *args: Any) -> str:
        return "bin/widish"

Widish = closed.Category(python.Ty, Process)

def shell_runner_ob(ob: closed.Ty) -> type:
    if ob == Language:
        return IO
    return object


def shell_runner_ar(ar):
    if isinstance(ar, Data):
        t = _lazy(Process.run_constant, ar)
    elif isinstance(ar, Swap):
        t = partial(Process.run_swap, ar)
    elif isinstance(ar, Copy):
        t = partial(Process.run_copy, ar)
    elif isinstance(ar, Merge):
        t = partial(Process.run_merge, ar)
    elif isinstance(ar, Discard):
        t = partial(Process.run_discard, ar)
    elif isinstance(ar, Exec):
         t = _lazy(Process.deferred_exec, ar)
    elif isinstance(ar, Program):
         t = _lazy(Process.run_program, ar)
    elif isinstance(ar, Eval):
         t = _lazy(Process.deferred_exec, ar)
    else:
        t = _lazy(Process.deferred_exec, ar)

    dom = SHELL_RUNNER(ar.dom)
    cod = SHELL_RUNNER(ar.cod)
    res = Process(t, dom, cod)
    res.ar = ar
    return res

class WidishFunctor(closed.Functor):
    def __init__(self):
        super().__init__(
            shell_runner_ob,
            shell_runner_ar,
            dom=Computation,
            cod=Widish
        )

SHELL_RUNNER = WidishFunctor()
