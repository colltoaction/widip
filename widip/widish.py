from functools import partial
from subprocess import run
import sys
from discopy.utils import tuplify, untuplify
from discopy import closed, python

def _run_subprocess(args, input_str=None):
    return run(args, check=True, text=True, capture_output=True, input=input_str).stdout.rstrip("\n")

def _split_args(ar, args):
    n = len(ar.dom)
    return args[:n], args[n:]

def _run_constant(ar, *args):
    _, params = _split_args(ar, args)
    return untuplify(params) if params else ("" if ar.dom == closed.Ty() else ar.dom.name)

def _run_map(ar, *args):
    b, params = _split_args(ar, args)
    return untuplify(tuple(untuplify(kv(*tuplify(params))) for kv in b))

def _run_seq(ar, *args):
    b, params = _split_args(ar, args)
    return untuplify(b[1](*tuplify(b[0](*tuplify(params)))))

def _run_default(ar, *args):
    b, params = _split_args(ar, args)
    return _run_subprocess((ar.name,) + b, "\n".join(params) if params else None)

def _run_widip(ar, *args):
    b, params = _split_args(ar, args)
    return _run_subprocess((sys.executable, "-m", "widip") + b, "\n".join(params) if params else None)

SHELL_RUNNER = closed.Functor(
    lambda ob: str,
    lambda ar: {
        "widip": partial(partial, _run_widip, ar),
        "⌜−⌝": partial(partial, _run_constant, ar),
        "(||)": partial(partial, _run_map, ar),
        "(;)": partial(partial, _run_seq, ar),
    }.get(ar.name, partial(partial, _run_default, ar)),
    cod=closed.Category(python.Ty, python.Function))
