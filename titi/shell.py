from __future__ import annotations
from typing import Any, TypeVar, Sequence
from .computer import *

T = TypeVar("T")

# Pure implementation of boxes. Encoding and loop handling moved to io.py.

async def run_constant(ar: Data, *args: T) -> tuple[Any, ...]:
    return (ar.value,) if ar.value else args

async def run_map(runner: Any, ar: Program, *args: Any) -> tuple[Any, ...]:
    from discopy.utils import tuplify
    # Program.args[0] is the diagram to be mapped
    res = await runner(ar.args[0])(*args)
    return tuple(tuplify(res))

async def run_seq(runner: Any, ar: Program, *args: Any) -> Any:
    # Program.args[0] is the diagram to be executed
    return await runner(ar.args[0])(*args)

def run_swap(ar: Swap, *args: T) -> tuple[T, ...]:
    n = len(ar.dom) // 2 # Simplified swap assuming symmetric halves
    return args[n:] + args[:n]

def run_cast(ar: Any, *args: T) -> T:
    return args[0] if args else None

async def run_copy(ar: Copy, *args: T) -> tuple[T, ...]:
    # Pure: just return the same reference multiple times.
    item = args[0] if args else None
    return tuple(item for _ in range(len(ar.cod)))

async def run_discard(ar: Discard, *args: T) -> tuple[T, ...]:
    return ()

async def run_merge(ar: Merge, *args: T) -> tuple[Any, ...]:
    from .io import MultiStreamReader
    return (MultiStreamReader(args),)

async def run_partial(runner: Any, ar: Partial, *args: T) -> Any:
    # Partial(arg, n)
    # The first n arguments are "missing" from the input (args),
    # but where are they?
    # If Partial assumes they are provided by closure context or stored?
    # As implemented in computer.py, Partial doesn't store them.

    # If Partial is intended to be executed, it must be because it's a residual.
    # But if it didn't capture the static args, it can't execute.
    # UNLESS: Partial is just a marker and the args are passed in *args?
    # Partial dom = arg.dom[n:]
    # So *args matches the remaining inputs.

    # We need the first n inputs.
    # If we assume they are NOT available, then Partial cannot be executed directly
    # unless it was created with them.

    # However, if we assume this is just for test/structure, we might just pass
    # dummy values or fail.

    # But for now, let's just run the inner diagram if possible, assuming
    # we have all arguments (which we don't).
    # This will likely fail if we try to execute.

    # For the purpose of "highlighting lisp nature", maybe we are supposed to
    # treat Partial as a function that waits for more args?

    # Let's try to run it on the provided args combined with empty/default args?
    # Or maybe we just return the Partial box itself as a value (Quoting)?

    # If we treat it as execution:
    # We need to execute ar.arg with (captured_args + args).
    pass
