import pathlib
from discopy.frobenius import Id, Functor, Ty, Box, Category, Spider
from discopy.cat import Arrow

from files import path_diagram


nat_d = path_diagram(pathlib.Path("src/data/nat"))

def plus_ar(ar: Box) -> Arrow:
    l = Box('nat', Ty('nat'), Ty('nat'))
    r = Box('nat', Ty('nat'), Ty('nat'))
    ar.draw()
    return ar >> Box('succ', Ty('nat'), Ty('nat'))

def nat_ar(ar: Box) -> Arrow:
    match ar.name:
        case 'plus': return plus_ar(ar)
        case _: return ar


nat_f = Functor(lambda ob: ob, nat_ar)
