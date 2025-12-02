from functools import partial
from subprocess import CalledProcessError, run

from discopy.closed import Category, Functor, Ty, Box, Eval
from discopy import python


io_ty = Ty("io")

def run_native_subprocess(ar, *b):
    def run_native_subprocess_constant(*params):
        return params[0] if params else ar.dom.name if ar.dom else ""
    def run_native_subprocess_map(*params):
        print("map", b, params)
        return b[0](params[0]), b[1](params[1])
    def run_native_subprocess_seq(*params):
        print("seq", b, params)
        print("b[0](*params)", b[0](*params))
        print("b[1](b[0](*params))", b[1](b[0](*params)))
        return b[1]((b[0](*params)))
    def run_native_subprocess_inside(inp, *args):
        print("run", inp, args)
        try:
            io_result = run(
                args,
                check=True, text=True, capture_output=True,
                input=inp)
            res = io_result.stdout.rstrip("\n")
            return res
        except CalledProcessError as e:
            return e.stderr
    if ar.name == "⌜−⌝":
        return run_native_subprocess_constant
    if ar.name == "(||)":
        return run_native_subprocess_map
    if ar.name == "(;)":
        return run_native_subprocess_seq
    if ar.name == "G":
        return partial(run_native_subprocess_inside, run_native_subprocess_constant())

SHELL_RUNNER = Functor(
    lambda ob: str,
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
