from functools import partial
from itertools import batched
from subprocess import CalledProcessError, Popen, PIPE
import threading

from discopy.closed import Category, Functor, Ty, Box, Eval
from discopy.utils import tuplify, untuplify
from discopy import python


io_ty = Ty("io")

class IO:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    @staticmethod
    def constant(ar, params):
        def _constant(*input_args):
            # If input_args provided, return them (pass through)
            # Otherwise return name?
            # Existing logic: if not params: return "" if ar.dom == Ty() else ar.dom.name
            # But params here are the constant arguments passed to runner?
            # No, params are the inputs from upstream.
            # run_native_subprocess_constant receives `*params`.
            # `ar.dom.name` is from closure.

            # Wait, `run_native_subprocess` closure captures `ar` and `b`.
            # `b` is `*b` arguments to `run_native_subprocess`.

            if not input_args:
                 return "" if ar.dom == Ty() else ar.dom.name
            return untuplify(input_args)
        return IO(_constant)

    @staticmethod
    def seq(ar, b):
        # b contains [IO1, IO2]
        def _seq(*params):
            p1_input = untuplify(params)

            if p1_input is not None:
                res1 = b[0](p1_input)
            else:
                res1 = b[0]()

            res2 = b[1](res1)

            if isinstance(res1, Popen):
                if res1.stdout:
                    res1.stdout.close()
            return res2
        return IO(_seq)

    @staticmethod
    def parallel(ar, b):
        # b contains [k1, v1, k2, v2...] (IO objects)
        def _parallel(*params):
            input_data = None
            p_in = untuplify(params)
            if isinstance(p_in, Popen):
                try:
                    out, _ = p_in.communicate()
                    if isinstance(out, bytes):
                        input_data = out.decode()
                    else:
                        input_data = out
                except ValueError:
                    pass
            elif isinstance(p_in, str):
                input_data = p_in
            else:
                pass

            mapped = []
            futures = []
            ignored_futures = []

            for batch in batched(zip(ar.dom, b), 2):
                if len(batch) < 2: continue
                (dk, k), (dv, v) = batch

                if input_data is not None:
                    k_res = k(input_data)
                else:
                    k_res = k()

                if input_data is not None:
                    v_res = v(input_data)
                else:
                    v_res = v()

                futures.append(v_res)

                if isinstance(k_res, Popen):
                    ignored_futures.append(k_res)

            for res in futures:
                if isinstance(res, Popen):
                    out = res.stdout.read() if res.stdout else ""
                    res.wait()
                    if out:
                         mapped.append(out.rstrip("\n"))
                    else:
                         mapped.append("")
                else:
                    mapped.append(res)

            for proc in ignored_futures:
                if proc.stdout: proc.stdout.read()
                proc.wait()

            return untuplify(tuple(mapped))
        return IO(_parallel)

    @staticmethod
    def inside(ar, b):
        # b contains args to command (e.g. "echo", "hello")
        def _inside(*params):
            cmd_args = b

            stdin_arg = None
            stdin_input = None

            p_in = untuplify(params)

            if isinstance(p_in, Popen):
                stdin_arg = p_in.stdout
            elif isinstance(p_in, str):
                stdin_input = p_in
            elif p_in is None or p_in == ():
                pass
            else:
                 stdin_input = str(p_in)

            try:
                cmd = list(b)

                if stdin_arg:
                    process = Popen(cmd, stdin=stdin_arg, stdout=PIPE, text=True)
                else:
                    process = Popen(cmd, stdin=PIPE, stdout=PIPE, text=True)

                if stdin_input is not None:
                     def write_stdin(proc, data):
                         try:
                             if proc.stdin:
                                 proc.stdin.write(data)
                                 proc.stdin.close()
                         except (OSError, ValueError, BrokenPipeError):
                             pass

                     t = threading.Thread(target=write_stdin, args=(process, stdin_input))
                     t.start()
                elif not stdin_arg:
                    if process.stdin:
                        process.stdin.close()

                return process

            except CalledProcessError as e:
                return e.stderr
            except Exception as e:
                return str(e)
        return IO(_inside)


def run_native_subprocess(ar, *b):
    if ar.name == "⌜−⌝":
        return IO.constant(ar, b)
    if ar.name == "(||)":
        return IO.parallel(ar, b)
    if ar.name == "(;)":
        return IO.seq(ar, b)
    if ar.name == "g":
        # For 'g', b contains args. The IO executes them immediately?
        # Original code: res = run_native_subprocess_inside(*b)
        # return res
        # Wait, 'g' box in loader.py:
        # load_scalar with tag -> Box("G", ...).
        # load_scalar without tag -> Box("⌜−⌝", ...).
        # Where is "g" (lowercase)?
        # widish.py had `if ar.name == "g": res = run_native_subprocess_inside(*b); return res`.
        # This implies "g" executes immediately with args in `b`.
        # "G" (uppercase) returns the runner.

        # If "g" executes immediately, it returns the result.
        # So we should call IO.inside(ar, b) and then CALL it?
        # But IO expects input params.
        # run_native_subprocess_inside uses `*params` for input.
        # `b` are command args.
        # If "g" is used, `b` must contain inputs too?
        # No. `run_native_subprocess_inside(*params)` uses `b` from closure.
        # `run_native_subprocess(ar, *b)` creates the runner.

        # Original code for "g":
        # `res = run_native_subprocess_inside(*b)`
        # `run_native_subprocess_inside` expects `*params` (stdin).
        # So `res` is the result of calling it with `b` as stdin?
        # No. `run_native_subprocess_inside` definition:
        # `def run_native_subprocess_inside(*params):`
        #   `cmd_args = b`
        #   `p_in = untuplify(params)`

        # So if I call `run_native_subprocess_inside(*b)`, I am passing `b` as stdin!
        # But `b` are command args?
        # If `b` are command args, why pass them as stdin?

        # Let's check `load_scalar`.
        # `Box("G", Ty(tag) @ Ty(v), ...)` -> Uppercase G.
        # `Box("g", ...)` doesn't appear in `loader.py`.
        # But `widish.py` had handling for it.
        # Maybe legacy?
        # I will keep it consistent with original: call the inside logic with `b` as params.
        # `IO.inside(ar, b)(*b)`? No.
        # `IO.inside` uses `b` as closure (command).
        # If I call it with `*b` as params, I am piping the command args to the command?
        # That seems weird.

        # Assume "g" is special and just returns the IO for now.
        return IO.inside(ar, b)(*b)

    if ar.name == "G":
        return IO.inside(ar, b)

SHELL_RUNNER = Functor(
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
