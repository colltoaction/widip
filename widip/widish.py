from functools import partial
from itertools import batched
from subprocess import CalledProcessError, Popen, PIPE
import threading

from discopy.closed import Category, Functor, Ty, Box, Eval
from discopy.utils import tuplify, untuplify
from discopy import python


io_ty = Ty("io")

def run_native_subprocess(ar, *b):
    def run_native_subprocess_constant(*params):
        if not params:
            return "" if ar.dom == Ty() else ar.dom.name
        return untuplify(params)

    def run_native_subprocess_map(*params):
        # Parallel execution: (||)
        # params: shared stdin (either string or Popen or empty)
        # b: list of (KeyRunner, ValueRunner) pairs flattened

        input_data = None

        # Determine the input source
        p_in = untuplify(params)
        if isinstance(p_in, Popen):
            try:
                # We use communicate() here because p_in is an input pipe to US.
                # If p_in's stdin was closed by previous step, communicate is fine.
                # But if p_in is a process we are reading from, we read stdout.
                # communicate reads stdout.
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

        # Launch all processes
        for batch in batched(zip(ar.dom, b), 2):
            if len(batch) < 2:
                continue
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

        # Collect results
        for res in futures:
            if isinstance(res, Popen):
                # Avoid communicate() because stdin might be closed by thread
                out = res.stdout.read() if res.stdout else ""
                # We could also read stderr here
                res.wait()
                if out:
                     mapped.append(out.rstrip("\n"))
                else:
                     mapped.append("")
            else:
                mapped.append(res)

        # Cleanup ignored futures
        for proc in ignored_futures:
            if proc.stdout:
                proc.stdout.read() # Consume to avoid buffer filling
            proc.wait()
        
        return untuplify(tuple(mapped))

    def run_native_subprocess_seq(*params):
        # Sequential: b[0] >> b[1]
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

    def run_native_subprocess_inside(*params):
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

    if ar.name == "⌜−⌝":
        return run_native_subprocess_constant
    if ar.name == "(||)":
        return run_native_subprocess_map
    if ar.name == "(;)":
        return run_native_subprocess_seq
    if ar.name == "g":
        res = run_native_subprocess_inside(*b)
        return res
    if ar.name == "G":
        return run_native_subprocess_inside

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
