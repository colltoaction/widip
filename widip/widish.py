import asyncio

from collections.abc import Callable
from functools import partial
from discopy.utils import tuplify, untuplify
from discopy import closed, python, utils

from .computer import *
from .thunk import thunk, unwrap

class Process(python.Function):
    def __init__(self, inside, dom, cod):
        super().__init__(inside, dom, cod)
        self.type_checking = False

    def then(self, other):
        from discopy.utils import tuplify, untuplify
        steps = []
        for p in [self, other]:
            if hasattr(p, "_steps"): steps.extend(p._steps)
            else: steps.append(p)
        
        async def piped(*args):
            res = args
            for p in steps:
                res = await unwrap(p(*tuplify(res)))
                if res == (): return ()
            return untuplify(res)
        
        new_p = Process(piped, self.dom, other.cod)
        new_p._steps = steps
        return new_p

    def tensor(self, other):
        from discopy.utils import tuplify, untuplify
        parts = []
        for p in [self, other]:
            if hasattr(p, "_parts"): parts.extend(p._parts)
            else: parts.append(p)
            
        async def tensored(*args):
            current_idx = 0
            thunks = []
            for p in parts:
                dom_len = len(p.dom)
                p_args = args[current_idx : current_idx + dom_len]
                thunks.append(thunk(p, *p_args))
                current_idx += dom_len
            
            results = await unwrap(tuple(thunks))
            final_res = tuple(item for r in results for item in tuplify(r))
            return final_res
            
        new_p = Process(tensored, self.dom + other.dom, self.cod + other.cod)
        new_p._parts = parts
        return new_p

    @classmethod
    def eval(cls, base, exponent, left=True):
        async def func(f, *x):
             return await unwrap(f(*x))
        return Process(
            func,
            (exponent << base) @ base,
            exponent
        )

    @staticmethod
    def split_args(ar, *args):
        n = len(ar.dom)
        return args[:n], args[n:]

    @classmethod
    async def run_node(cls, node, *args):
        from discopy import closed
        from .compiler import Program
        from .yaml import Alias
        
        if isinstance(node, (Program, Alias)):
             return await cls.run_command(node.name, getattr(node, "args", ()), args)

        if isinstance(node, closed.Diagram):
             from .widish import SHELL_RUNNER, fold_diagram
             node = fold_diagram(SHELL_RUNNER(node))
        
        if callable(node):
            return await unwrap(node(*args))
        
        # Original command execution path
        return await cls.run_command(node, (), args)

    @classmethod
    async def run_map(cls, ar, *args):
        b, params = cls.split_args(ar, *args)
        # return a function that returns a tuple of results
        async def composed(*x):
             results = [cls.run_node(kv, *tuplify(x)) for kv in b]
             return untuplify(tuple([await unwrap(r) for r in results]))
        return composed

    @classmethod
    async def run_seq(cls, ar, *args):
        b, params = cls.split_args(ar, *args)
        if not b: return args
        
        res = await cls.run_node(b[0], *tuplify(args))
        for func in b[1:]:
            res = await cls.run_node(func, *tuplify(res))
        return res

    @classmethod
    async def run_swap(cls, ar, *args):
        n_left = len(ar.left)
        return untuplify(args[n_left:] + args[:n_left])

    @classmethod
    async def run_cast(cls, ar, *args):
        b, params = cls.split_args(ar, *args)
        func = b[0]
        return func

    @classmethod
    async def run_copy(cls, ar, *args):
        val = args[0] if args else ""
        if val is None:
             return (None,) * ar.n
        return untuplify(tuple([val] * ar.n))

    @classmethod
    async def run_discard(cls, ar, *args):
        return ()

    @classmethod
    async def run_data(cls, ar, *args):
        if any(x is None for x in args):
             return (None,)
        return (ar.value,)

    @classmethod
    async def run_command(cls, name, args, stdin):
        from .compiler import SHELL_COMPILER
        from .yaml import RECURSION_REGISTRY
        from discopy.utils import tuplify, untuplify
        from pathlib import Path

        if not name:
             return stdin[0] if stdin else ""
        
        # Propagate dead branch
        if any(x is None for x in stdin):
             return (None,)

        # No expansion: $ is not part of widish according to user.
        expanded_args = args

        if not isinstance(name, str):
             return await unwrap(name(*(tuplify(expanded_args) + tuplify(stdin))))

        # Check recursion registry
        if name in (registry := RECURSION_REGISTRY.get()):
             item = registry[name]
             if not isinstance(item, (Process, Callable)):
                  from .widish import SHELL_RUNNER, fold_diagram
                  compiled = SHELL_COMPILER(item)
                  runner = fold_diagram(SHELL_RUNNER(compiled))
                  registry[name] = runner
                  RECURSION_REGISTRY.set(dict(registry))
             else:
                  runner = item
             return await unwrap(runner(*(tuplify(expanded_args) + tuplify(stdin))))

        # Evaluate arguments for external command
        cmd = [name]
        cmd_args = []
        current_stdin = stdin
        for arg in expanded_args:
             # Run the arg as a filter on current inputs
             res = await unwrap(Process.run_node(arg, *tuplify(current_stdin)))
             # Flatten result and append to command args
             for item in tuplify(res):
                  cmd_args.append(str(item))

        cmd += cmd_args

        # print(f"DEBUG: run_command {cmd} stdin={stdin}")
        if len(cmd) > 1 or " " in name:
            import os
            shell = os.environ.get("WIDIP_SHELL", "sh -c").split()
            cmd = shell + [" ".join(cmd)]

        process = await asyncio.create_subprocess_exec(
            cmd[0], *cmd[1:],
            stdout=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        input_data = "\n".join(stdin).encode() if stdin else None
        stdout, stderr = await process.communicate(input=input_data)
        if stderr:
             import sys
             print(stderr.decode(), file=sys.stderr)
        
        if process.returncode != 0:
             return ()

        res = stdout.decode().rstrip("\n")
        return res

    @classmethod
    async def deferred_exec(cls, ar, *args):
        async_b, async_params = map(unwrap, map(tuplify, cls.split_args(ar, *args)))
        b, params = await asyncio.gather(async_b, async_params)
        name, cmd_args = (
            (ar.name, b) if ar.name
            else (b[0], b[1:]) if b
            else (None, ())
        )
        
        if name is None:
             return params[0] if params else ""

        if callable(name):
             # If the "name" is a function, call it directly
             return await unwrap(name(*(tuplify(cmd_args) + tuplify(params))))

        result = await cls.run_command(name, cmd_args, params)
        return result if ar.cod else ()

    @staticmethod
    async def run_program(ar, *args):
        # ar is the Program box, args is the pipeline stdin
        return await Process.run_command(ar.name, ar.args, args)

    @staticmethod
    def run_constant_gamma(ar, *args):
        return ("bin/widish",)

Widish = closed.Category(python.Ty, Process)

def shell_runner_ar(ar):
    if isinstance(ar, Data):
        t = thunk(Process.run_data, ar)
    elif isinstance(ar, Concurrent):
        t = thunk(Process.run_map, ar)
    elif isinstance(ar, Pair):
        t = thunk(Process.run_seq, ar)
    elif isinstance(ar, Sequential):
        t = thunk(Process.run_seq, ar)
    elif isinstance(ar, Swap):
        t = thunk(Process.run_swap, ar)
    elif isinstance(ar, Cast):
        t = thunk(Process.run_cast, ar)
    elif isinstance(ar, Copy):
        t = thunk(Process.run_copy, ar)
    elif isinstance(ar, Discard):
        t = thunk(Process.run_discard, ar)
    elif isinstance(ar, Exec):
         gamma = Constant(dom=closed.Ty())
         diagram = gamma @ closed.Id(ar.dom) >> Eval(ar.dom, ar.cod)
         return SHELL_RUNNER(diagram)
    elif isinstance(ar, Constant):
         t = thunk(Process.run_constant_gamma, ar)
    elif isinstance(ar, Program):
         t = thunk(Process.run_program, ar)
    elif isinstance(ar, closed.Eval):
         return Process.eval(ar.base, ar.exponent, ar.left)
    elif isinstance(ar, Eval):
         t = thunk(Process.deferred_exec, ar)
    else:
        t = thunk(Process.deferred_exec, ar)

    return Process(t, python.Ty(tuple([object] * len(ar.dom))), python.Ty(tuple([object] * len(ar.cod))))

def fold_diagram(diagram):
    if isinstance(diagram, Process):
        return diagram

    procs = []
    for layer in diagram.inside:
        layer_process = None
        if len(layer.boxes_and_offsets) == 1 and layer.boxes_and_offsets[0][1] == 0:
             layer_process = layer.boxes_and_offsets[0][0]
        else:
             for b, offset in layer.boxes_and_offsets:
                  if layer_process is None:
                       layer_process = b
                  else:
                       layer_process = layer_process.tensor(b)
        if layer_process:
            procs.append(layer_process)

    if not procs:
        async def identity(*x): return untuplify(x)
        return Process(identity, diagram.dom, diagram.dom)

    if len(procs) == 1:
        return procs[0]

    async def iterative_runner(*x):
        res = x
        for p in procs:
            res = await unwrap(p(*tuplify(res)))
            if res == (): return ()
        return untuplify(res)

    return Process(iterative_runner, diagram.dom, diagram.cod)

class WidishFunctor(closed.Functor):
    def __init__(self):
        super().__init__(
            lambda ob: python.Ty(tuple([object] * len(ob))),
            shell_runner_ar,
            dom=Computation,
            cod=Widish
        )

SHELL_RUNNER = WidishFunctor()
