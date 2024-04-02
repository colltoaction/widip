from src.data.nat import zero, succ, plus_box
from .rep import py_functor


py_nat_f = py_functor(
    lambda ar: {
        zero.name: lambda: 0,
        succ.name: lambda x: int(x) + 1,
        plus_box.name: lambda *xs: sum(xs),}[ar.name],)
