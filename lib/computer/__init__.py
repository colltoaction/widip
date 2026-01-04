from typing import Any
from discopy.frobenius import Id, Functor, Ty, Box, Category, Spider
from discopy.cat import Arrow
from .core import Language, Language2, Data, Program, service_map, Titi, Discard, Copy, Merge, Computation, Partial, eval_diagram, eval_python
from .common import TitiBox

def replace_box(box: Box) -> Functor:
    return replace_arrow(box, box.name)

def replace_arrow(ar: Arrow, name) -> Functor:
    boxes = {
        Box(name, box.dom, box.cod): box
        for box in ar.boxes}
    return Functor(
        lambda ob: Ty("") if ob == Ty(name) else ob,
        lambda ar: boxes.get(ar, ar))

# Anchor management for recursive execution
_anchor_store: dict[str, Any] = {}

def get_anchor(name: str) -> Any | None:
    """Get an anchor by name, or None if not found."""
    return _anchor_store.get(name)

def set_anchor(name: str, value: Any) -> None:
    """Set an anchor value."""
    _anchor_store[name] = value
