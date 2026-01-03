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
