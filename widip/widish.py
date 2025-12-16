import sys
import os
import threading
from functools import partial
from itertools import batched
from subprocess import Popen, PIPE
from collections.abc import Callable

from discopy.closed import Category, Functor, Ty, Box, Eval, Exp
from discopy.monoidal import Functor as MonoidalFunctor
from discopy.utils import tuplify, untuplify
from discopy import python


io_ty = Ty("io")

def pump(input_f, output_fs, close_input=False):
    try:
        while True:
            chunk = input_f.read(1024)
            if not chunk:
                break
            for f in output_fs:
                try:
                    f.write(chunk)
                    f.flush()
                except (IOError, ValueError):
                    pass
    except (IOError, ValueError):
        pass
    finally:
        for f in output_fs:
            try:
                f.close()
            except (IOError, ValueError):
                pass
        if close_input:
            try:
                input_f.close()
            except (IOError, ValueError):
                pass

class ProcessGroup:
    def __init__(self, processes):
        self.processes = processes

    def __call__(self, stdin=None):
        if stdin is None or len(self.processes) <= 1:
            return tuple(p(stdin=stdin) for p in self.processes)

        children = []
        for p_factory in self.processes:
            children.append(p_factory(stdin=PIPE))

        output_fs = []
        for c in children:
            if hasattr(c, "stdin") and c.stdin:
                output_fs.append(c.stdin)
            elif isinstance(c, (list, tuple)):
                for item in c:
                    if hasattr(item, "stdin") and item.stdin:
                        output_fs.append(item.stdin)
                        break
        # Detach stdin from children so communicate() doesn't close them
        for c in children:
            if hasattr(c, "stdin"):
                c.stdin = None
            elif isinstance(c, (list, tuple)):
                for item in c:
                    if hasattr(item, "stdin"):
                        item.stdin = None

        # Duplicate stdin for the thread
        input_f = stdin
        close_input = False
        try:
            fd = os.dup(stdin.fileno())
            input_f = os.fdopen(fd, "r")
            close_input = True
        except (ValueError, OSError):
            # Fallback if stdin is not a real file
            pass

        t = threading.Thread(target=pump, args=(input_f, output_fs, close_input))
        t.daemon = True
        t.start()

        return tuple(children)

class WidishFunctor(MonoidalFunctor):
    def __call__(self, other):
        if isinstance(other, Exp):
            return self.cod.ob((self.ob[other],))
        return super().__call__(other)

def run_native_subprocess(ar, *b):
    def run_native_subprocess_constant(*params, **kwargs):
        if not params:
            return "" if ar.dom == Ty() else ar.dom.name
        return untuplify(params)

    def run_native_subprocess_map(*params, stdin=None):
        mapped = []
        for (dk, k), (dv, v) in batched(zip(ar.dom, b), 2):
            def chain(stdin=stdin, k=k, v=v):
                p_k = k(*tuplify(params), stdin=stdin)

                stdin_v = None
                detached_k = []

                if hasattr(p_k, "stdout") and p_k.stdout:
                    stdin_v = p_k.stdout
                elif isinstance(p_k, (list, tuple)):
                    detached_k = list(p_k)

                p_v = v(stdin=stdin_v)

                if hasattr(p_k, "stdout") and p_k.stdout:
                    p_k.stdout.close()
                    p_k.stdout = None

                res = []
                if isinstance(p_k, (list, tuple)):
                    res.extend(p_k)
                elif hasattr(p_k, "stdin"):
                    res.append(p_k)
                res.append(p_v)
                return tuple(res)
            mapped.append(chain)
        return ProcessGroup(tuple(mapped))

    def run_native_subprocess_seq(*params, stdin=None):
        def lazy_seq(stdin=stdin):
            p1 = b[0](stdin=stdin)
            p2 = b[1](stdin=p1.stdout)
            p1.stdout.close()
            return p2
        return lazy_seq

    def run_native_subprocess_inside(*params, stdin=None):
        def lazy_popen(stdin=stdin):
            process = Popen(
                b,
                text=True,
                stdout=PIPE,
                stderr=sys.stderr,
                stdin=stdin or PIPE
            )
            if params and process.stdin:
                for p in params:
                    process.stdin.write(p + "\n")
                process.stdin.close()
                process.stdin = None
            return process
        return lazy_popen

    if ar.name == "⌜−⌝":
        return run_native_subprocess_constant
    if ar.name == "(||)":
        return run_native_subprocess_map()
    if ar.name == "(;)":
        return run_native_subprocess_seq()
    if ar.name == "g":
        return run_native_subprocess_inside(*b)
    if ar.name == "G":
        return run_native_subprocess_inside(*b)

SHELL_RUNNER = WidishFunctor(
    lambda ob: object,
    lambda ar: partial(run_native_subprocess, ar),
    cod=Category(python.Ty, python.Function))


SHELL_COMPILER = Functor(
    # lambda ob: Ty() if ob == Ty("io") else ob,
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
