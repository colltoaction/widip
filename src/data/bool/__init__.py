from discopy.frobenius import Id, Functor, Ty, Box, Category, Spider
from src import box_fun_functor

def bool_ar(ar):
    requirements = {
        'true': lambda ar: lambda: True,
        'false': lambda ar: lambda: False,
    }
    r = requirements.get(ar.name, None)
    # TODO xs no es siempre, por ejemplo si
    # viene de un closed cable.
    # dependiendo del box cambia el lambda
    # no es siempre id
    return r(ar) if r else lambda *xs: xs

bool_f = box_fun_functor(bool_ar)
