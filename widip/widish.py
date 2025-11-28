from functools import partial
from subprocess import CalledProcessError, run

from discopy.closed import Category, Functor, Ty, Box, Eval
from discopy import python


io_ty = Ty("io")

def run_native_subprocess(ar, *b):
    def run_native_subprocess_map():
        print(b)
        return lambda x: (b[0](x), b[1](x))
    def run_native_subprocess_seq():
        # TODO call in sequence
        # print("seq", b, )
        return lambda x: b[1](b[0](x))
    def run_native_subprocess_inside():
        # print("run", b)
        try:
            io_result = run(
                b[1:],
                check=True, text=True, capture_output=True,
                input=b[0])
            res = io_result.stdout.rstrip("\n")
            return res
        except CalledProcessError as e:
            return e.stderr
    # TODO create a pipeline using input parameters
    # to the run function
    if ar.name == "⌜−⌝":
        return lambda x: b[0]
    if ar.name == "(||)":
        return run_native_subprocess_map()
    if ar.name == "(;)":
        return run_native_subprocess_seq()
    return run_native_subprocess_inside()

SHELL_RUNNER = Functor(
    lambda ob: str,
    lambda ar: lambda *a:
        # TODO preprocess sequences and parallels
        run_native_subprocess(ar, *a),
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
    diagram
    return diagram
    return diagram.curry(2, left=False)
    diagram = (diagram @ diagram.cod.exponent) >> Eval(diagram.cod)
