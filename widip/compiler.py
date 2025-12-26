from functools import reduce
from discopy import closed
from discopy.closed import Id, Ty, Curry, Diagram
from .computer import Computation, Swap, Cast, Copy, Data, Sequential, Concurrent, Eval

def unwrap(ty):
    # Ty wrapping usually happens when box.dom is accessed.
    # Ty.inside gives the list of Objects.
    # If ty is already Object (Over), we want it directly.
    # Ob has inside which is (self,).
    # So ty.inside[0] returns self. Safe.
    return ty.inside[0] if isinstance(ty, closed.Ty) and hasattr(ty, 'inside') and ty.inside else ty

def adapt(source, target):
    if source == target: return Id(source)
    if len(source) == 1 and len(target) > 1: return Copy(source, target)
    return Cast(source, target)

def compile_sequential(box):
    A, B = map(unwrap, box.dom)
    x, y, u, z = A.exponent, A.base, B.exponent, B.base

    # We want A @ B @ x -> z (Over codomain)
    # curry(n=len(x), left=False) takes x from right.
    return (Id(Ty(A)) @ Swap(Ty(B), x)
            >> Eval(A) @ Id(Ty(B))
            >> Swap(y, Ty(B))
            >> Id(Ty(B)) @ adapt(y, u)
            >> Eval(B)).curry(n=len(x), left=False)

def compile_concurrent(box):
    if not box.dom: return Id(Ty())
    if len(box.dom) == 1: return Id(box.dom)

    Fs = [unwrap(t) for t in box.dom]
    Xs, Ys = [f.exponent for f in Fs], [f.base for f in Fs]

    # Diagram: F1...FN @ X1...XN -> Y1...YN
    # curry(left=False) takes Xs from right.

    def layer(state, i):
        diag, ys = state
        F_rest = Ty().tensor(*Fs[i+1:])
        X_rest = Ty().tensor(*Xs[i+1:])

        step = Id(ys @ Fs[i]) @ Swap(F_rest, Xs[i]) @ Id(X_rest) \
               >> Id(ys) @ Eval(Fs[i]) @ Id(F_rest @ X_rest)

        return (diag >> step, ys @ Ys[i])

    diagram, _ = reduce(layer, range(len(Fs)), (Id(box.dom) @ Id(Ty().tensor(*Xs)), Ty()))
    return diagram.curry(n=len(Ty().tensor(*Xs)), left=False)

SHELL_COMPILER = closed.Functor(
    ob=lambda x: x,
    ar=lambda f: {Sequential: compile_sequential, Concurrent: compile_concurrent}.get(type(f), lambda x: x)(f),
    dom=Computation,
    cod=closed.Category(closed.Ty, Diagram)
)

def compile_shell_program(diagram):
    diagram = SHELL_COMPILER(diagram)

    if diagram.dom != Ty():
        gens = [Data(Ty(), Ty(t)) for t in diagram.dom.inside]
        diagram = reduce(lambda a, b: a @ b, gens) >> diagram

    return diagram
