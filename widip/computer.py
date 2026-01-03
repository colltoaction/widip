from __future__ import annotations
import contextvars
from typing import Any
from pathlib import Path
from discopy import closed, monoidal, symmetric
from . import yaml, loader

from .thunk import unwrap, recurse
import sys

# Symbols are represented by ℙ
Language = closed.Ty("ℙ")

RECURSION_REGISTRY: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar("recursion", default={})

class Eval(closed.Eval):
    def __init__(self, base: closed.Ty, exponent: closed.Ty):
        super().__init__(base, exponent)

class Curry(closed.Curry):
    def __init__(self, arg: closed.Diagram, n: int = 1, left: bool = True):
        super().__init__(arg, n, left)

class Data(closed.Box):
    def __init__(self, value: Any, dom: closed.Ty = closed.Ty(), cod: closed.Ty = closed.Ty()):
        self.value = value
        content = str(value) if value else "-"
        name = f"⌜{content if len(content) < 100 else content[:97] + '...'}⌝"
        super().__init__(name, dom, cod)

class Program(closed.Box):
    def __init__(self, name: str, dom: closed.Ty = closed.Ty(), cod: closed.Ty = closed.Ty(), args: Any = ()):
        super().__init__(name, dom, cod)
        self.args = args

class Copy(closed.Box):
    def __init__(self, x: closed.Ty, n: int = 2):
        super().__init__("Δ", x, x ** n)
        self.draw_as_spider = True

class Merge(closed.Box):
    def __init__(self, x: closed.Ty, n: int = 2):
        super().__init__("μ", x ** n, x)
        self.draw_as_spider = True

class Discard(closed.Box):
    def __init__(self, x: closed.Ty):
        super().__init__("ε", x, closed.Ty())
        self.draw_as_spider = True

class Partial(closed.Box):
    def __init__(self, arg: closed.Diagram, n: int = 1, left: bool = True):
        self.arg, self.n, self.left = arg, n, left
        name = f"Part({arg.name}, {n})"
        dom, cod = arg.dom[n:], arg.cod
        super().__init__(name, dom, cod)

class Swap(closed.Box):
    def __init__(self, x: closed.Ty, y: closed.Ty):
        super().__init__("σ", x @ y, y @ x)
        self.draw_as_swap = True

Computation = closed.Category()

# --- Compiler Logic ---



def compiler(diagram, comp, path):
    res = None
    match diagram:
        case closed.Diagram() | closed.Box():
            res = diagram
        case _ if callable(diagram) and not isinstance(diagram, (monoidal.Diagram, monoidal.Box)):
             res = Program(getattr(diagram, '__name__', 'func'), 
                           Language, Language, (diagram,))
        case yaml.Scalar():
             args = (diagram.value,) if diagram.value else ()
             tag = diagram.tag
             res = Program(tag, Language ** len(diagram.dom), Language ** len(diagram.cod), args) if tag else \
                   Data(diagram.value, Language ** len(diagram.dom), Language ** len(diagram.cod))
        case yaml.Sequence() | yaml.Mapping():
             diag = comp(diagram.inside, comp, path)
             if diagram.tag:
                 static_args = None
                 if all(isinstance(box, (Data, Copy, Swap, Merge, Discard)) for box in diag.boxes):
                     static_args = tuple(box.value for box in diag.boxes if isinstance(box, Data))
                 
                 args = static_args if static_args is not None else (diag,)
                 res = Program(diagram.tag, Language ** len(diagram.dom), Language ** len(diagram.cod), args)
             else:
                 res = diag
        case yaml.Anchor():
             anchors = RECURSION_REGISTRY.get().copy()
             compiled = comp(diagram.inside, comp, path)
             anchors[diagram.name] = compiled
             RECURSION_REGISTRY.set(anchors)
             res = Program(diagram.name, Language ** len(diagram.dom), Language ** len(diagram.cod), (compiled,))
        case yaml.Alias():
             res = Program(diagram.name, Language ** len(diagram.dom), Language ** len(diagram.cod))
        case loader.Swap():
             res = Swap(Language ** len(diagram.dom[0:1]), Language ** len(diagram.dom[1:2]))
        case loader.Copy():
             res = Copy(Language ** len(diagram.dom), len(diagram.cod))
        case loader.Merge():
             res = Merge(Language ** len(diagram.cod), len(diagram.dom))
        case loader.Discard():
             res = Discard(Language ** len(diagram.dom))
        case monoidal.Box():
             res = closed.Id(Language ** len(diagram.dom))
        case symmetric.Diagram() | monoidal.Diagram():
             res = closed.Id(Language ** len(diagram.dom))
             for box, offset in zip(diagram.boxes, diagram.offsets):
                 if isinstance(box, (Data, Program, Copy, Merge, Discard, Swap, closed.Box)):
                     compiled = box
                 elif isinstance(box, closed.Diagram):
                     compiled = box
                 else:
                     compiled = comp(box, comp, path)
                 
                 left_id = closed.Id(res.cod[:offset])
                 right_id = closed.Id(res.cod[offset + len(compiled.dom):])
                 
                 try:
                     layer = left_id.tensor(compiled, right_id)
                     res = res >> layer
                 except Exception:
                     res = res >> (closed.Id(res.cod[:offset]) @ compiled @ closed.Id(res.cod[offset+len(compiled.dom):]))
        case _:
             res = closed.Id(closed.Ty())

    if isinstance(res, closed.Box):
         res = closed.Id(res.dom) >> res
    
    if path is not None and __debug__ and not isinstance(diagram, (closed.Diagram, closed.Box)):
        from .files import diagram_draw
        diagram_draw(Path(path).with_suffix(".shell.yaml"), res)
    
    return res

async def interpreter(pipeline: Any, 
                      source: Any, 
                      loop: Any, 
                      output_handler: Any):
    """Unified execution loop. Pure in essence, delegating IO to handlers."""
    async for fd, path, input_stream in source:
        try:
            runner_process = pipeline(fd)
            
            async def compute(rec, *args):
                    inp = (input_stream,) if runner_process.dom else ()
                    res = await runner_process(*inp)
                    # Unwrap returns either the value or a tuple of values
                    final = await unwrap(loop, res)
                    await output_handler(rec, final)
                    return final

            await recurse(compute, None, loop)

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            if __debug__: raise e
