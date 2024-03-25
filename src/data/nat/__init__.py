from discopy.frobenius import Id, Functor, Ty, Box, Category, Spider
from discopy.cat import Arrow


plus_box = Box("plus", Ty("nat") @ Ty("nat"), Ty("nat"))
zero = Box("0", Ty(), Ty("nat"))
succ = Box("succ", Ty("nat"), Ty("nat"))
two = zero >> succ >> succ


def plus_ar(ar: Box) -> Arrow:
    l = Box('nat', Ty('nat'), Ty('nat'))
    r = Box('nat', Ty('nat'), Ty('nat'))
    return ar >> Box('succ', Ty('nat'), Ty('nat'))

def nat_ar(ar: Box) -> Arrow:
    match ar.name:
        case 'plus': return plus_ar(ar)
        case _: return ar


nat_f = Functor(lambda ob: ob, nat_ar)
