import pytest
from discopy import closed
from computer import Language
from computer.super import Language2
from computer.hyper import ackermann

def test_ackermann_structure():
    """Test that ackermann is a closed.Box."""
    assert isinstance(ackermann, closed.Box)
    assert ackermann.dom == Language2
    assert ackermann.cod == Language
    assert ackermann.name == "ackermann"

def test_ackermann_signature():
    """Test that ackermann has the correct type signature."""
    # ackermann: Language @ Language → Language
    # Which is (ℙ, ℙ) → ℙ
    assert len(ackermann.dom) == 2
    assert len(ackermann.cod) == 1
    assert all(obj.name == "ℙ" for obj in ackermann.dom)
    assert all(obj.name == "ℙ" for obj in ackermann.cod)
