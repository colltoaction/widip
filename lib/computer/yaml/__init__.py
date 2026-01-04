from __future__ import annotations
from typing import Any
import discopy
from discopy import frobenius, closed

from .parse import parse, impl_parse
from . import representation as ren
from .representation import Scalar, Sequence, Mapping, Alias, Document, Stream, Titi
from . import construct as con
from . import presentation as pres
from ..core import Language

# --- Composable Helper ---

class Composable:
    """Helper to allow functor-like functions to be composed with >>."""
    def __init__(self, fn):
        self._fn = fn
    def __call__(self, *args, **kwargs):
        return self._fn(*args, **kwargs)
    def __rshift__(self, other):
        # f >> g -> g(f(x))
        return Composable(lambda *args, **kwargs: other(self(*args, **kwargs)))

# --- Presentation Singletons ---

get_node_data = pres.GetNodeData()
step = pres.Step()
iterate = pres.Iterate()

# --- Compose Functor ---

def compose_dispatch(box: Any) -> frobenius.Diagram:
    """Manual dispatcher for serialization items."""
    if hasattr(box, 'kind'):
         kind = box.kind
         if kind == "Scalar": return ren.Scalar(box.tag, box.value)
         if kind == "Alias": return ren.Alias(box.anchor_name)
    return box

_compose_functor_obj = frobenius.Functor(ob={frobenius.Ty("Node"): ren.Node}, ar=compose_dispatch)
compose_functor = Composable(lambda diag: _compose_functor_obj(diag))

def compose(node_wire):
    """Traceable compose diagram."""
    return frobenius.Box("compose", frobenius.Ty("Node"), ren.Node)(node_wire)

# --- Construct Functor ---

class MapAll:
    """Helper to map all objects to the same base atom as Language (P)."""
    def __init__(self, target_ob): self.target_ob = target_ob
    def __getitem__(self, _): return self.target_ob
    def get(self, _, default=None): return self.target_ob
    def __contains__(self, _): return True
    def __iter__(self): return iter([])

def construct_dispatch(box: Any) -> closed.Diagram:
    # Always normalize the result to the Language category (closed)
    n_dom = len(getattr(box, 'dom', []))
    n_cod = len(getattr(box, 'cod', []))
    target_dom = Language ** n_dom
    target_cod = Language ** n_cod

    if isinstance(box, ren.YamlBox):
        res = con.construct_box(box)
    elif isinstance(box, closed.Box) and not isinstance(box, frobenius.Box):
        res = box >> closed.Id(box.cod)
    else:
        # Default for unidentified wires/atoms
        return closed.Id(target_dom)
            
    return res

# Extract base Ob from Language ensuring it's not a nested Ty
P_OB = Language[0].inside[0] if hasattr(Language[0], 'inside') else Language[0]
if isinstance(P_OB, closed.Ty): P_OB = P_OB[0] # Handle variations in DisCoPy Ty structure

# Original Functor that maps everything to the base Language atom
_construct_functor_obj = closed.Functor(
    ob=MapAll(P_OB), 
    ar=construct_dispatch, 
    cod=closed.Category()
)

def _construct_functor_wrapped(diag: Any) -> closed.Diagram:
    if isinstance(diag, list):
        # Default to tensor product for plain lists
        res = None
        for item in diag:
            d = _construct_functor_wrapped(item)
            res = d if res is None else res @ d
        return res or closed.Id(closed.Ty())
    return _construct_functor_obj(diag)

# Exposed as a composable functor
construct_functor = Composable(_construct_functor_wrapped)

# --- Load Pipeline ---
load = lambda source: construct_functor(compose_functor(impl_parse(source)))
