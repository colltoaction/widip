from __future__ import annotations
from discopy import closed

# Symbols are represented by ℙ
Language = closed.Ty("ℙ")

# --- Computer Primitives ---

Data = lambda value, dom=closed.Ty(), cod=Language: \
    closed.Box(f"⌜{value}⌝", dom, cod, data=value)

Program = lambda name, dom=Language, cod=Language, args=(): \
    closed.Box(name, dom, cod, data=args)

Discard = lambda x=Language: \
    closed.Box("ε", x, closed.Ty(), draw_as_spider=True)

from .composition import Sequential, Parallel
Computation = closed.Category(closed.Ty, closed.Diagram)
