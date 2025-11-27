from subprocess import CalledProcessError, run

from discopy.closed import Category, Functor, Ty, Box, Eval
from discopy import python


io_ty = Ty("io")

def run_native_subprocess(ar, *b):
    def run_native_subprocess_seq(inp=None, *subprocess_args):
        b0out = b[0](inp, subprocess_args[0])
        b1out = b[1](b0out, subprocess_args[1])
        return b1out
    def run_native_subprocess_map(inp=None, *subprocess_args):
        b0out = b[0](inp, *subprocess_args[:-1])
        b1out = b[1](inp, *subprocess_args[-1:])
        return lambda u, v: b0out + b1out
    def run_native_subprocess_inside(inp=None, *subprocess_args):
        try:
            io_result = run(
                b,
                check=True, text=True, capture_output=True,
                input=inp)
            return io_result.stdout
        except CalledProcessError as e:
            return e.stderr
    # TODO create a pipeline using input parameters
    # to the run function
    if ar.name == "(;)":
        return run_native_subprocess_seq
    if ar.name == "(||)":
        return run_native_subprocess_map
    return run_native_subprocess_inside

SHELL_RUNNER = Functor(
    lambda ob: str,
    lambda ar: lambda *a:
        # TODO preprocess sequences and parallels
        run_native_subprocess(ar, *a),
    cod=Category(python.Ty, python.Function))


SHELL_COMPILER = Functor(
    lambda ob: ob,
    lambda ar: {
        # "ls": ar.curry().uncurry()
    }.get(ar.name, ar),)
        # print(ar) or ar.curry().uncurry() if ar.name not in ("(;)", "(||)") else ar)
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
    return diagram
    diagram = (diagram @ diagram.cod.exponent) >> Eval(diagram.cod)
