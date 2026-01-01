import asyncio

from functools import partial
from discopy.utils import tuplify, untuplify
from discopy import closed

from .computer import *
from .thunk import thunk, unwrap


def split_args(ar, *args):
    n = len(ar.dom)
    return args[:n], args[n:]

async def run_native_subprocess_constant(ar, *args):
    b, params = split_args(ar, *args)
    if not params:
        if not ar.dom:
            # Return cod names as value if dom is empty
            if hasattr(ar, "cod") and ar.cod:
                 return untuplify(tuple(x.name for x in ar.cod))
            return ()
        result = ar.dom.name
        return result
    return untuplify(await unwrap(params))

def run_native_subprocess_map(ar, *args):
    b, params = split_args(ar, *args)
    return untuplify(tuple(kv(*tuplify(params)) for kv in b))

def run_native_subprocess_seq(ar, *args):
    b, params = split_args(ar, *args)
    if not b:
        return params

    res = b[0](*tuplify(params))
    for func in b[1:]:
        res = func(*tuplify(res))
    return res

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

async def run_command(name, args, stdin):
    process = await asyncio.create_subprocess_exec(
        name, *args,
        stdout=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    input_data = None
    if stdin:
         if isinstance(stdin, str):
             input_data = stdin.encode()
         else:
             input_data = "\n".join(stdin).encode()

    stdout, stderr = await process.communicate(input=input_data)
    
    if process.returncode != 0:
        import sys
        sys.stderr.write(f"ERROR: command '{name}' failed with {process.returncode}\n")
        sys.stderr.write(f"STDERR: {stderr.decode()}\n")
        
    return stdout.decode().rstrip("\n")

async def _deferred_exec_subprocess(ar, *args):
    async_b, async_params = map(unwrap, map(tuplify, split_args(ar, *args)))
    b, params = await asyncio.gather(async_b, async_params)
    
    
    # b corresponds to ar.dom inputs. ar.dom[0] is program wire.
    if not b:
        # Should not happen for Eval
        name, cmd_args = None, ()
        stdin_data = None
    else:
        name = b[0].name if hasattr(b[0], 'name') else str(b[0])
        
        # Distinguish stdin vs args based on types in ar.dom
        # ar.dom[0] is Program (Language).
        # subsequent inputs are arguments or stdin.
        # We assume Language (Ty("IO")) indicates stdin.
        
        cmd_args = []
        stdin_data = None
        
        # b[1:] matches ar.dom[1:]
        # We need to handle index bounds safely
        if len(b) > 1:
            for val, ty in zip(b[1:], ar.dom[1:]):
                # Language is Ty("IO"). 
                # Note: ty coming from domain might be Ty(Ob("IO")) or just Ob("IO").
                # Check name or equality.
                is_io = (ty == Language) or (isinstance(ty, type(Language)) and getattr(ty, "name", "") == "IO") or getattr(ty, "name", "") == "IO"
                
                if is_io:
                      # Stdin input
                      if stdin_data is None:
                          stdin_data = val
                      else:
                          if isinstance(stdin_data, str) and isinstance(val, str):
                              stdin_data += val
                          else:
                               # Fallback for weird types
                               stdin_data = str(stdin_data) + str(val)
                else:
                      # Argument
                      cmd_args = list(cmd_args) + [str(val)]
                      
        cmd_args = tuple(cmd_args)
        
    # params (inputs beyond ar.dom) are usually empty for Eval unless logic changes.
    # If params exist, treat as extra stdin?
    if params:
        p_str = "".join(str(p) for p in params)
        if stdin_data is None:
            stdin_data = p_str
        else:
            stdin_data += p_str

    result = await run_command(name, cmd_args, stdin_data)
    return result if ar.cod else ()

def run_program(ar, *args):
    return ar.name

def run_constant_gamma(ar, *args):
    return "bin/widish"

def shell_runner_ar(ar):
    if isinstance(ar, Data):
        t = thunk(run_native_subprocess_constant, ar)
    elif isinstance(ar, Concurrent):
        t = thunk(run_native_subprocess_map, ar)
    elif isinstance(ar, Pair):
        t = thunk(run_native_subprocess_seq, ar)
    elif isinstance(ar, Sequential):
        t = thunk(run_native_subprocess_seq, ar)
    elif isinstance(ar, Swap):
        t = partial(run_native_swap, ar)
    elif isinstance(ar, Cast):
        t = thunk(run_native_cast, ar)
    elif isinstance(ar, Copy):
        t = partial(run_native_copy, ar)
    elif isinstance(ar, Discard):
        t = partial(run_native_discard, ar)
    elif isinstance(ar, Exec):
         gamma = Constant()
         diagram = gamma @ closed.Id(ar.dom) >> Eval(ar.dom, ar.cod)
         return SHELL_RUNNER(diagram)
    elif isinstance(ar, Constant):
         t = thunk(run_constant_gamma, ar)
    elif isinstance(ar, Program):
         t = thunk(run_program, ar)
    elif isinstance(ar, Eval):
         t = thunk(_deferred_exec_subprocess, ar)
    else:
        t = thunk(_deferred_exec_subprocess, ar)

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
