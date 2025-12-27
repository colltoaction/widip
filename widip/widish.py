import asyncio

from discopy.utils import tuplify, untuplify
from discopy import closed

from .computer import *
from .thunk import thunk, unwrap


def split_args(ar, *args):
    n = len(ar.dom)
    return args[:n], args[n:]

async def run_native_subprocess_constant(ar, *args):
    # Data box.
    b, params = split_args(ar, *args)

    input_values = await unwrap(tuplify(b))

    if ar.name == "Scalar":
        # Untagged scalar. Return the input value.
        if input_values:
            return input_values[0]
        # If no input values (dom=Ty()), return None
        return None
    else:
        # Tagged scalar. ar.name is the command.
        parts = ar.name.split()
        cmd = parts[0]
        extra_args = parts[1:]

        cmd_args = list(extra_args)

        for v in input_values:
            if v is not None:
                cmd_args.append(str(v))

        try:
            result = await run_command(cmd, cmd_args, [])
            return result
        except Exception:
            return ""

async def run_native_subprocess_map(ar, *args):
    # Concurrent box. Maps to Mapping.
    items = await unwrap(args)
    d = {}

    for i in range(0, len(items), 2):
        if i+1 < len(items):
            key = items[i]
            val = items[i+1]
            try:
                d[key] = val
            except TypeError:
                d[str(key)] = val

    return d

async def run_native_subprocess_seq(ar, *args):
    items = await unwrap(args)
    return list(items)

def run_native_swap(ar, *args):
    n_left = len(ar.left)
    n_right = len(ar.right)
    left_args = args[:n_left]
    right_args = args[n_left : n_left + n_right]
    return untuplify(right_args + left_args)

def run_native_cast(ar, *args):
    b, params = split_args(ar, *args)
    func = b[0]
    return func

def run_native_copy(ar, *args):
    b, params = split_args(ar, *args)
    return b * ar.n

def run_native_discard(ar, *args):
    return ()

async def run_native_trace(ar, *args):
    return ()

async def run_command(name, args, stdin):
    cmd_args = [str(a) for a in args]
    stdin_data = [str(s) for s in stdin] if stdin else []

    try:
        process = await asyncio.create_subprocess_exec(
            name, *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        input_data = "\n".join(stdin_data).encode() if stdin_data else None
        stdout, stderr = await process.communicate(input=input_data)

        if process.returncode != 0:
             pass

        return stdout.decode().rstrip("\n")
    except FileNotFoundError:
        return "" # Command not found

async def _deferred_exec_subprocess(ar, *args):
    # Generic box (tag on sequence/mapping)
    b, params = split_args(ar, *args)
    _b = await unwrap(tuplify(b))

    # Pass inputs as arguments
    cmd_args = [str(x) for x in _b if x is not None]

    command_parts = ar.name.split()
    cmd = command_parts[0]
    extra_args = command_parts[1:]

    full_args = extra_args + cmd_args

    result = await run_command(cmd, full_args, [])

    if not ar.cod:
        return ()
    return result

def _deferred_exec_subprocess_task(ar, *args):
    return asyncio.create_task(_deferred_exec_subprocess(ar, *args))

def shell_runner_ar(ar):
    if isinstance(ar, Data):
        t = thunk(run_native_subprocess_constant, ar)
    elif isinstance(ar, Concurrent):
        t = thunk(run_native_subprocess_map, ar)
    elif isinstance(ar, Sequential):
        t = thunk(run_native_subprocess_seq, ar)
    elif isinstance(ar, Swap):
        t = thunk(run_native_swap, ar)
    elif isinstance(ar, Cast):
        t = thunk(run_native_cast, ar)
    elif isinstance(ar, Copy):
        t = thunk(run_native_copy, ar)
    elif isinstance(ar, Discard):
        t = thunk(run_native_discard, ar)
    elif isinstance(ar, Trace):
        t = thunk(run_native_trace, ar)
    else:
        t = thunk(_deferred_exec_subprocess_task, ar)

    dom = SHELL_RUNNER(ar.dom)
    cod = SHELL_RUNNER(ar.cod)
    return Process(t, dom, cod)

class WidishFunctor(closed.Functor):
    def __init__(self):
        super().__init__(
            lambda ob: object,
            shell_runner_ar,
            dom=Computation,
            cod=Widish
        )

SHELL_RUNNER = WidishFunctor()
