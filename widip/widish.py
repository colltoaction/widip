from subprocess import run

from discopy.frobenius import Category, Functor, Ty, Box
from discopy.frobenius import Hypergraph as H
from discopy import python


io_ty = Ty("io")

def run_native_subprocess(ar, *a):
    # TODO unnamed cables/empty strings are dropped
    # if not x == Ty("")
    assert ar.name == "run" and ar.dom[0] == io_ty
    a = "".join(a)
    io_result = run(
        tuple(str(x) for x in ar.dom[1:]),
        check=True, input=a, text=True, capture_output=True)
    return io_result.stdout


class IORun(python.Function):
    @classmethod
    def spiders(cls, n_legs_in: int, n_legs_out: int, typ: Ty):
        def step(*io_inputs):
            assert len(io_inputs) == n_legs_in
            io_output = "".join(io_inputs)
            return (io_output, ) * n_legs_out
        return IORun(
            inside=step,
            dom=tuple(str for _ in range(n_legs_in)),
            cod=tuple(str for _ in range(n_legs_out)))

 
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
