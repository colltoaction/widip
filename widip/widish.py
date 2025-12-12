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

        # Launch all processes
        for (dk, k), (dv, v) in batched(zip(ar.dom, b), 2):
            # In mapping, k is the key (constant), v is the value (command).
            # The structure from load_mapping is (Key @ Value).
            # We want to run Value with the shared input.
            # But what about Key? Key usually ignores input and returns name.

            # Execute key runner
            # It seems Key doesn't need stdin usually.
            if input_data is not None:
                # If we pass input to key runner, it might just return it if it's constant runner logic
                k_res = k(input_data)
            else:
                k_res = k()

            # Execute value runner
            # Value runner (command) definitely needs the input.
            if input_data is not None:
                v_res = v(input_data)
            else:
                v_res = v()

            futures.append(v_res)
            # We assume mapping returns only values?
            # Or does it return pairs?
            # Original code: mapped.append(untuplify(res)) where res = v(...)
            # Original code ignored k_res for the result list?
            # No: b0 = k(...); res = v(b0); mapped.append(res).
            # Original code chained k output to v input!

            # This is crucial.
            # If `k` is "cat1", `v` is `!cat`.
            # `k` returns "cat1".
            # `v` runs `cat` with input "cat1".
            # Result is "cat1".

            # If so, `input_data` (stdin from outside) is LOST in original code unless `k` preserves it.
            # `run_native_subprocess_constant` returns `params` if params is not empty.
            # So if `params` (stdin) is provided, `k` returns stdin.
            # Then `v` gets stdin.
            # So the chaining IS how stdin is propagated.

            # So my change to call `v(input_data)` directly is correct IF `k` is just a pass-through for input.
            # But what if `k` does something else?
            # `k` is a runner.
            # If `k` is a constant box `⌜−⌝`, `run_native_subprocess_constant` logic:
            # `if not params: return name`.
            # `return params`.
            # So if `input_data` is provided, `k` returns `input_data`.

            # So calling `v(input_data)` is equivalent to `v(k(input_data))` for constants.
            # So the logic holds.

            # However, I am appending `v_res` to futures.
            # But original code returned `untuplify(tuple(mapped))`.
            # Where `mapped` contained results of `v`.
            # So I should only append `v_res`?
            # But wait, does `(||)` return just values or key-values?
            # `load_mapping` uses `Box("(||)", ob.cod, exps << bases)`.
            # `exps` comes from values. `bases` comes from keys.
            # It seems it returns both? Or just one?
            # `exps << bases`. This is function type.
            # The *codomain* of the box determines the output type of the function.
            # If `exps << bases` corresponds to `B << A`, function returns `B`.
            # `bases` are inputs (from keys?). `exps` are outputs (from values?).
            # So the function returns results corresponding to `exps`.
            # So yes, only `v` outputs are returned.

        # Collect results
        for res in futures:
            if isinstance(res, Popen):
                try:
                    out, _ = res.communicate()
                    if out is None:
                         out = ""
                    mapped.append(out.rstrip("\n"))
                except ValueError:
                    mapped.append("")
            else:
                mapped.append(res)
        
        return untuplify(tuple(mapped))

    def run_native_subprocess_seq(*params):
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
