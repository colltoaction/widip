from functools import partial, cache
from subprocess import CalledProcessError, run
from collections.abc import Iterator

from discopy.utils import tuplify
from discopy import closed, python


io_ty = closed.Ty("io")

def force(x):
    while callable(x):
        x = x()
    if isinstance(x, (Iterator, tuple, list)):
        # Recursively force items in iterator or sequence
        x = tuple(map(force, x))

    # "untuplify" logic: unwrap singleton tuple/list
    if isinstance(x, (tuple, list)) and len(x) == 1:
        return x[0]
    return x

def split_args(ar, args):
    n = len(ar.dom)
    return args[:n], args[n:]

def run_native_subprocess_constant(ar, *args):
    b, params = split_args(ar, args)
    if not params:
        # If domain is empty (Ty()), return empty tuple () instead of ""
        # to match codomain length 0.
        if ar.dom == closed.Ty():
            return ()
        return ar.dom.name
    return force(params)

def run_native_subprocess_map(ar, *args):
    b, params = split_args(ar, args)
    mapped = []
    for kv in b:
        res = kv(*tuplify(params))
        mapped.append(res)
    # Use force to unwrap singleton list if necessary
    return force(tuple(mapped))

def run_native_subprocess_seq(ar, *args):
    b, params = split_args(ar, args)
    b0 = b[0](*tuplify(params))
    b1 = b[1](*tuplify(b0))
    # Return thunk directly (laziness preserved)
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
    # Replace tuple(map(force, ...)) with force(...)
    _b = force(b)
    _params = force(params)

    # Ensure they are tuples for _run_command (which expects tuples/lists for args/stdin)
    # force() unwraps singleton tuples.
    # _run_command expects 'args' and 'stdin' to be joinable sequences.
    # If _b is a single string "foo", _run_command((name,)+("foo")) works?
    # No, (name,) + "foo" -> Error.
    # If _b is "foo", we need ("foo",).
    # So we need to re-tuplify if force unwrapped it?

    # Wait, _run_command signature:
    # def _run_command(name, args, stdin):
    #    (name,) + args
    #    "\n".join(stdin)

    # If args is "foo" (string). (name,) + "foo" -> Error.
    # If args is ("foo",). (name,) + ("foo",) -> (name, "foo"). Correct.
    # If args is (). (name,) + () -> (name,). Correct.

    # So _run_command requires 'args' to be a TUPLE.
    # 'force' UNWRAPS singleton tuples.
    # So force(("foo",)) -> "foo".
    # So _b becomes "foo".
    # So we MUST tuplify _b before passing to _run_command.

    # Same for _params (stdin).
    # "\n".join(stdin).
    # If stdin is "foo". "foo" is iterable of chars.
    # "\n".join("foo") -> "f\no\no".
    # This is WRONG if we meant one line "foo".
    # We want "\n".join(("foo",)) -> "foo".

    # So 'force' is actually TOO aggressive for this specific use case if used directly?
    # Or we should use tuplify() on the result of force()?

    _b = tuplify(force(b))
    _params = tuplify(force(params))

    result = _run_command(ar.name, _b, _params)

    if not ar.cod:
        return ()
    return result

def _exec_subprocess(ar, *args):
    return partial(_deferred_exec_subprocess, ar, args)

SHELL_RUNNER = closed.Functor(
    lambda ob: str,
    lambda ar: {
        "⌜−⌝": partial(partial, run_native_subprocess_constant, ar),
        "(||)": partial(partial, run_native_subprocess_map, ar),
        "(;)": partial(partial, run_native_subprocess_seq, ar),
    }.get(ar.name, partial(partial, _exec_subprocess, ar)),
    cod=closed.Category(python.Ty, python.Function))


SHELL_COMPILER = closed.Functor(
    lambda ob: ob,
    lambda ar: {
        # "ls": ar.curry().uncurry()
    }.get(ar.name, ar),)
    # TODO remove .inside[0] workaround
    # lambda ar: ar)


def compile_shell_program(diagram):
    """
    close input parameters (constants)
    drop outputs matching input parameters
    all boxes are io->[io]"""
    # TODO compile sequences and parallels to evals
    diagram = SHELL_COMPILER(diagram)
    return diagram
