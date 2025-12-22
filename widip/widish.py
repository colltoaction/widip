from collections.abc import Iterator
from functools import cache, partial
from subprocess import run

from discopy.utils import tuplify
from discopy import closed, python


def thunk(f, *args):
    return partial(partial, f, *args)

@cache
def _force_call(thunk):
    while callable(thunk):
        thunk = thunk()
    return thunk

def force(x):
    x = _force_call(x)
    if isinstance(x, (Iterator, tuple, list)):
        # Recursively force items in iterator or sequence
        x = tuple(map(force, x))
    
    # "untuplify" logic: unwrap singleton tuple/list
    if isinstance(x, (tuple, list)) and len(x) == 1:
        return x[0]
    return x

def split_args(ar, *args):
    n = len(ar.dom)
    return args[:n], args[n:]

def run_native_subprocess_constant(ar, *args):
    b, params = split_args(ar, *args)
    if not params:
        if ar.dom == closed.Ty():
            return ()
        return ar.dom.name
    return force(params)

def run_native_subprocess_map(ar, *args):
    b, params = split_args(ar, *args)
    return force(kv(*tuplify(params)) for kv in b)

def run_native_subprocess_seq(ar, *args):
    b, params = split_args(ar, *args)
    b0 = b[0](*tuplify(params))
    b1 = b[1](*tuplify(b0))
    return b1

def _run_command(name, args, stdin):
    io_result = run(
        (name,) + args,
        check=True, text=True, capture_output=True,
        input="\n".join(stdin) if stdin else None,
        )
    return io_result.stdout.rstrip("\n")

def _deferred_exec_subprocess(ar, *args):
    b, params = split_args(ar, *args)
    _b = tuplify(force(b))
    _params = tuplify(force(params))
    result = _run_command(ar.name, _b, _params)
    if not ar.cod:
        return ()
    return result


SHELL_RUNNER = closed.Functor(
    lambda ob: str,
    lambda ar: {
        "⌜−⌝": thunk(run_native_subprocess_constant, ar),
        "(||)": thunk(run_native_subprocess_map, ar),
        "(;)": thunk(run_native_subprocess_seq, ar),
    }.get(ar.name, thunk(_deferred_exec_subprocess, ar)),
    cod=closed.Category(python.Ty, python.Function))
