from discopy.frobenius import Id, Functor, Ty, Box, Category, Spider
from src.yaml import frobenius_function_functor

def nat_ar(ar):
    requirements = {
        '0': lambda ar: lambda: 0,
        'succ': lambda ar: lambda x: x+1,
        'plus': lambda ar: lambda *xs: sum(xs),
    }
    r = requirements.get(ar.name, None)
    # TODO xs no es siempre, por ejemplo si
    # viene de un closed cable.
    # dependiendo del box cambia el lambda
    # no es siempre id
    return r(ar) if r else lambda *xs: xs

nat_f = frobenius_function_functor(nat_ar)
