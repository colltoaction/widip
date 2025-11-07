from subprocess import CalledProcessError, run

from discopy.frobenius import Category, Functor, Ty, Box, Bubble
from discopy.frobenius import Hypergraph as H
from discopy import python


io_ty = Ty("io")

def run_native_subprocess(ar, *a):
    # TODO unnamed cables/empty strings are dropped
    # if not x == Ty("")
    if type(ar) == Bubble:
        return run_native_subprocess(ar.arg, *a)
    try:
        io_result = run(
            tuple(str(x) for x in ar.dom[1:]),
            check=True, input=a[0], text=True, capture_output=True)
        return io_result.stdout
    except CalledProcessError as e:
        return e.stderr


class IORun(python.Function):
    __ambiguous_inheritance__ = True
    @classmethod
    def spiders(cls, n_legs_in: int, n_legs_out: int, typ: Ty):
        def step(*io_inputs):
            assert len(io_inputs) == n_legs_in
            io_output = "".join(io_inputs)
            return (io_output, ) * n_legs_out
        return python.Function(
            inside=step,
            dom=tuple(str for _ in range(n_legs_in)),
            cod=tuple(str for _ in range(n_legs_out)))

    @classmethod
    def bubble(cls, args, dom=None, cod=None):
        return python.Function(
            inside=args.inside,
            dom=dom,
            cod=cod)

 
SHELL_RUNNER = Functor(
    lambda ob: str,
    lambda ar: lambda *a:
        run_native_subprocess(ar, *a),
    cod=Category(python.Ty, IORun))


def command_io(diagram):
    """
    close input parameters (constants)
    drop outputs matching input parameters
    all boxes are io->[io]"""
    # print(diagram)
    # print(type(diagram))
    return (
        H.spiders(len(diagram.dom), 1, io_ty).to_diagram() @ H.spiders(0, 1, Ty(diagram.name)).to_diagram() @ H.spiders(0, 1, diagram.dom).to_diagram() >>
        Box("run",
            io_ty @ Ty(diagram.name) @ diagram.dom,
            io_ty) >>
        # TODO splitting into len(cod) copies more than needed
        H.spiders(1, len(diagram.cod), io_ty).to_diagram())

compile_shell_program = Functor(
    lambda x: io_ty,
    lambda b: command_io(b),)
