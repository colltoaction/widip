from discopy import closed

from widip.computer import Data, Parallel, Partial, Sequential, Ty, Uncurry
from widip.lang import Compile


def test_compile_sequential_operator_eq_2_7():
    """Eq. 2.7: `(;)` compiles to Curry/Eval over its typed bubble."""
    box = Sequential()
    source = box.bubble(dom=box.dom, cod=box.cod)
    operator = closed.Curry(source, n=len(box.dom), left=True)
    expected = (operator @ box.dom) >> closed.Eval(operator.cod)
    assert Compile().ar_map(box) == expected


def test_compile_parallel_operator_eq_2_7():
    """Eq. 2.7: `(||)` compiles to Curry/Eval over its typed bubble."""
    box = Parallel()
    source = box.bubble(dom=box.dom, cod=box.cod)
    operator = closed.Curry(source, n=len(box.dom), left=True)
    expected = (operator @ box.dom) >> closed.Eval(operator.cod)
    assert Compile().ar_map(box) == expected


def test_compile_partial_evaluator_fig_2_5():
    """Fig. 2.5: `[]` compiles as an operator bubble followed by evaluation."""
    box = Partial(Ty("Y"))
    source = box.bubble(dom=box.dom, cod=box.cod)
    operator = closed.Curry(source, n=len(box.dom), left=True)
    expected = (operator @ box.dom) >> closed.Eval(operator.cod)
    assert Compile().ar_map(box) == expected


def test_compile_data_idempotent_eq_2_8():
    """Eq. 2.8: quoting data compiles as Curry/Eval with empty context."""
    box = Data(Ty("A"))
    source = box.bubble(dom=Ty(), cod=box.cod)
    operator = closed.Curry(source, n=len(Ty()), left=True)
    expected = (operator @ Ty()) >> closed.Eval(operator.cod)
    assert Compile().ar_map(box) == expected


def test_compile_uncurry_sequential_eq_2_7():
    """Eq. 2.7: uncurried sequential composition compiles to Curry/Eval."""
    box = Uncurry(Sequential(), Ty("A"), Ty("C"))
    operator = closed.Curry(box.arg, n=len(box.dom), left=True)
    expected = (operator @ box.dom) >> closed.Eval(operator.cod)
    assert Compile().ar_map(box) == expected


def test_compile_uncurry_parallel_eq_2_7():
    """Eq. 2.7: uncurried parallel composition compiles to Curry/Eval."""
    box = Uncurry(Parallel(), Ty("A") @ Ty("U"), Ty("B") @ Ty("V"))
    operator = closed.Curry(box.arg, n=len(box.dom), left=True)
    expected = (operator @ box.dom) >> closed.Eval(operator.cod)
    assert Compile().ar_map(box) == expected
