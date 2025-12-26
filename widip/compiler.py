from functools import reduce
from discopy import closed
from discopy.closed import Id, Ty, Eval, Curry, Diagram
from .computer import Computation, Swap, Cast, Copy, Data, Sequential, Concurrent

def unwrap(ty):
    return ty.inside[0] if isinstance(ty, closed.Ty) and hasattr(ty, 'inside') and ty.inside else ty

def adapt(source, target):
    if source == target: return Id(source)
    if len(source) == 1 and len(target) > 1: return Copy(source, target)
    return Cast(source, target)

def compile_sequential(box):
    A, B = map(unwrap, box.dom)
    x, y, u, z = A.exponent, A.base, B.exponent, B.base

    # We want Over type (z << x). This requires left=True in curry.
    # left=True implies x is curried from the LEFT of the domain.
    # So internal diagram expects x @ A @ B.

    diagram = (Swap(x, Ty(A)) @ Id(Ty(B))
            >> Id(Ty(A)) @ Swap(x, Ty(B))
            >> Eval(A) @ Id(Ty(B)) # Eval(A) takes A @ x. Wait. x @ A?
            # Eval(Over) expects (y << x) @ x. So A @ x.
            # We have A @ x @ B.
            # Need to swap x back to right of A.

            # Let's trace carefully:
            # Input: x @ A @ B
            # Swap x, A -> A @ x @ B
            # Eval(A) takes A @ x.
            # So (Eval(A) @ Id(B)) consumes A @ x @ B -> y @ B.

            # Continue:
            >> Swap(y, Ty(B))
            >> Id(Ty(B)) @ adapt(y, u)
            >> Eval(B))

    return Curry(diagram, n=len(x), left=True)

def compile_concurrent(box):
    if not box.dom: return Id(Ty())
    if len(box.dom) == 1: return Id(box.dom)

    Fs = [unwrap(t) for t in box.dom]
    Xs, Ys = [f.exponent for f in Fs], [f.base for f in Fs]

    # We want Over type. left=True.
    # Internal diagram input: Xs @ Fs.
    # Xs = X1 @ X2 ...
    # Fs = F1 @ F2 ...

    # We need to pair Xi with Fi.
    # Xi is far left. Fi is far right.

    def layer(state, i):
        # State: diagram so far, and Types accumulated on left (Ys)
        diag, ys = state

        # Current wire state at step i:
        # ys @ X_rest @ F_rest
        # X_rest = Xi @ ...
        # F_rest = Fi @ ...

        # We want to move Xi next to Fi.
        # Xi is at start of X_rest.
        # Fi is at start of F_rest.
        # We need to swap Xi past (X_{i+1}...) to get to Fi?
        # No, we need to swap Xi past X_rest_others AND F_rest_others?
        # Actually, let's just maintain invariant:
        # ys @ Xi...Xn @ Fi...Fn

        F_i = Fs[i]
        X_i = Xs[i]

        X_rest = Ty().tensor(*Xs[i+1:])
        F_rest = Ty().tensor(*Fs[i+1:])

        # Current: ys @ Xi @ X_rest @ Fi @ F_rest
        # We want: ys @ yi @ X_rest @ F_rest

        # Step 1: Move Xi next to Fi.
        # Swap Xi past X_rest.
        # ys @ Xi @ X_rest @ Fi... -> ys @ X_rest @ Xi @ Fi...
        step1 = Id(ys) @ Swap(X_i, X_rest) @ Id(F_i @ F_rest)

        # Step 2: Swap Xi past Fi? No, Eval(Fi) takes Fi @ Xi.
        # We have ... @ Xi @ Fi ...
        # Swap Xi, Fi -> ... @ Fi @ Xi ...
        step2 = Id(ys @ X_rest) @ Swap(X_i, F_i) @ Id(F_rest)

        # Step 3: Eval(Fi)
        # Input: ys @ X_rest @ Fi @ Xi @ F_rest
        # Eval(Fi) takes Fi @ Xi -> Yi
        step3 = Id(ys @ X_rest) @ Eval(F_i) @ Id(F_rest)

        # Result: ys @ X_rest @ Yi @ F_rest
        # We want ys @ Yi @ X_rest @ F_rest to maintain invariant?
        # Or just accumulate Yi on left?
        # If we leave Yi where it is: ys @ X_rest @ Yi @ F_rest.
        # Next iteration X_{i+1} is at start of X_rest.
        # F_{i+1} is at start of F_rest.
        # Yi is between them.
        # We need to swap Yi past X_rest to left?
        # Swap X_rest, Yi -> Yi @ X_rest.
        step4 = Id(ys) @ Swap(X_rest, Ty(Ys[i])) @ Id(F_rest)

        # Result: ys @ Yi @ X_rest @ F_rest.
        # New ys = ys @ Yi.

        step = step1 >> step2 >> step3 >> step4

        return (diag >> step, ys @ Ys[i])

    # Initial state: Id(Xs @ Fs)
    diagram, _ = reduce(layer, range(len(Fs)), (Id(Ty().tensor(*Xs) @ box.dom), Ty()))
    return Curry(diagram, n=len(Ty().tensor(*Xs)), left=True)

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
