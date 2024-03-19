from discopy.frobenius import Id, Functor, Ty, Box, Category, Spider
from discopy.cat import Arrow


def unit_ar(ar: Box) -> Arrow:
    """takes a Diagram ast"""
    return Box('0', Ty(), Ty('nat'))

def succ_ar(ar: Box) -> Arrow:
    return ar >> Box('succ', Ty('nat'), Ty('nat'))

def plus_ar(ar: Box) -> Arrow:
    return ar >> Box('succ', Ty('nat'), Ty('nat'))

def nat_ar(ar: Box) -> Arrow:
    match ar.name:
        case '0': return unit_ar(ar)
        case 'succ': return succ_ar(ar)
        case 'plus': return plus_ar(ar)
        case _: return ar


nat_f = Functor(lambda ob: ob, nat_ar)
