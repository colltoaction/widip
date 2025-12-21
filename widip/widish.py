from functools import partial, cache
from subprocess import run

from discopy.utils import tuplify
from discopy import closed, python

from .compiler import force


io_ty = closed.Ty("io")

def split_args(ar, args):
    n = len(ar.dom)
    return args[:n], args[n:]

def run_native_subprocess_constant(ar, *args):
    b, params = split_args(ar, args)
    if not params:
        if ar.dom == closed.Ty():
            return ()
        return ar.dom.name
    return force(params)

def run_native_subprocess_map(ar, *args):
    b, params = split_args(ar, args)
    return force(kv(*tuplify(params)) for kv in b)

def run_native_subprocess_seq(ar, *args):
    b, params = split_args(ar, args)
    b0 = b[0](*tuplify(params))
    b1 = b[1](*tuplify(b0))
    return b1

@cache
def _run_command(name, args, stdin):
    io_result = run(
        (name,) + args,
        check=True, text=True, capture_output=True,
        input="\n".join(stdin) if stdin else None,
        )
    return io_result.stdout.rstrip("\n")

def _deferred_exec_subprocess(ar, args):
    b, params = split_args(ar, args)
    _b = tuplify(force(b))
    _params = tuplify(force(params))
    result = _run_command(ar.name, _b, _params)
    if not ar.cod:
        return ()
    return result


SHELL_RUNNER = closed.Functor(
    lambda ob: str,
    lambda ar: {
        "⌜−⌝": partial(partial, run_native_subprocess_constant, ar),
        "(||)": partial(partial, run_native_subprocess_map, ar),
        "(;)": partial(partial, run_native_subprocess_seq, ar),
    }.get(ar.name, partial(partial, lambda ar, *args: partial(_deferred_exec_subprocess, ar, args), ar)),
    cod=closed.Category(python.Ty, python.Function))
