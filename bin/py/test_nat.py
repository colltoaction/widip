from .nat import py_nat_f, zero, succ, plus_box

two = zero >> succ >> succ

def test_zero():
    assert py_nat_f(zero)() == 0

def test_two():
    assert py_nat_f(two)() == 2

def test_plus():
    four = two @ two >> plus_box
    assert py_nat_f(four)() == 4
