from functools import partial
from itertools import batched
from subprocess import run, CalledProcessError
from discopy.closed import Functor, Category, Ty
from discopy.utils import tuplify, untuplify
from discopy import python
from widip.box import ConstBox, RunBox

def shell_runner_mapping(ar):
    if isinstance(ar, ConstBox):
        # ConstBox returns a Program (P).
        # P = str -> unit.
        cmd = ar.value
        def program(arg_str):
             try:
                 run(
                    [cmd] if isinstance(cmd, str) else cmd,
                    input=arg_str,
                    capture_output=True,
                    text=True,
                    shell=True
                 )
                 return ()
             except Exception as e:
                 print(e)
                 return ()

        # The box takes inputs (Ty(v) -> str) and returns program.
        return lambda dummy_input: program

    if isinstance(ar, RunBox):
        # RunBox takes a Program and runs it.
        def run_it(prog):
            prog("")
            return ()
        return run_it

    if ar.name == "(||)":
        return partial(run_par, ar)

    if ar.name == "(;)":
        return partial(run_seq, ar)

    if ar.name == "g":
         # Execute directly.
         # Mapping: ar -> python function.
         # Python function takes inputs (corresponding to dom).
         # For "g", inputs are strings (commands).
         # It executes them.
         return lambda *args: run_inside(args)

    if ar.name == "G":
        # Return executor.
        # Inputs are strings (commands).
        # Returns a function (Program) that takes inputs (stdin) and runs.
        # This matches run_native_subprocess returning run_native_subprocess_inside.
        # run_native_subprocess captured *b (arguments to box).
        # And returned run_native_subprocess_inside which used b.

        return lambda *args: lambda *params: run_inside(args, params)

    # Fallback
    return lambda *args: None

def run_inside(cmd_args, input_args=None):
    """
    Executes subprocess.
    cmd_args: The arguments defining the command (from the diagram box inputs).
    input_args: The input string(s) to stdin (from the runtime program input).
    """
    try:
        # In original widish.py:
        # run_native_subprocess(ar, *b) captures b.
        # run_native_subprocess_inside(*params) uses b and params.
        # run(b, input="\n".join(params) if params else None)

        # Here cmd_args corresponds to b.
        # input_args corresponds to params.

        # run() takes list or string.
        # b (cmd_args) is a tuple of strings.
        # If it's a single string, we might want to pass it as such?
        # subprocess.run([arg1, arg2]) or "arg1 arg2" with shell=True.

        # Original used `b` directly as first arg to `run`.
        # `run(b, ...)`
        # If `b` is a tuple, `run` expects a list of args?
        # If `b` is `("echo", "hello")`, `run` executes `echo hello`.

        cmd = cmd_args

        inp = None
        if input_args:
             inp = "\n".join(input_args)

        io_result = run(
            cmd,
            check=True, text=True, capture_output=True,
            input=inp,
        )
        res = io_result.stdout.rstrip("\n")
        return res
    except CalledProcessError as e:
        return e.stderr
    except Exception as e:
        # Fallback
        return str(e)

def run_par(ar, *b):
    # b are the input programs
    def combined_program(*params):
        mapped = []
        for (dk, k), (dv, v) in batched(zip(ar.dom, b), 2):
            b0 = k(*tuplify(params))
            res = untuplify(v(*tuplify(b0)))
            mapped.append(untuplify(res))

        return untuplify(tuple(mapped))
    return combined_program

def run_seq(ar, *b):
    # b are the input programs
    def combined_program(*params):
        # b[0] is first program, b[1] is second
        b0 = b[0](*untuplify(params))
        res = untuplify(b[1](*tuplify(b0)))
        return res
    return combined_program

SHELL_RUNNER = Functor(
    lambda ob: str,
    shell_runner_mapping,
    cod=Category(python.Ty, python.Function)
)
