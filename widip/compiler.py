from __future__ import annotations
from .exec import Exec
from discopy import closed, monoidal, symmetric
from . import computer, yaml, loader
from pathlib import Path

def from_callable(dom: closed.Ty, cod: closed.Ty):
    """Decorator to convert a Python function into a closed.Diagram."""
    def decorator(f):
        if hasattr(closed.Diagram, 'from_callable'):
            return closed.Diagram.from_callable(f, dom, cod)
        # Fallback to a Program box if from_callable is missing
        return computer.Program(f.__name__, dom, cod, (f,))
    return decorator

def SHELL_COMPILER(diagram, compiler, path):
    atom = None
    res = None
    
    match diagram:
        # 0. Compiled Diagrams or Boxes
        case closed.Diagram() | closed.Box():
            return diagram

        # 1. Python callables (not yet converted)
        case _ if callable(diagram) and not isinstance(diagram, (monoidal.Diagram, monoidal.Box)):
             # Default to 0->1 or 1->1 if unknown? 
             # Actually, if it's not decorated, we treat it as a Scalar value or Program.
             atom = computer.Program(getattr(diagram, '__name__', 'func'), 
                                     computer.Language, computer.Language, (diagram,))

        # 2. Specific YAML source types
        case yaml.Scalar():
            args = (diagram.value,) if diagram.value else ()
            atom = computer.Program(diagram.tag, computer.Language ** len(diagram.dom), computer.Language ** len(diagram.cod), args) if diagram.tag else \
                   computer.Data(diagram.value, computer.Language ** len(diagram.dom), computer.Language ** len(diagram.cod))
        case yaml.Sequence() | yaml.Mapping():
            diag = compiler(diagram.inside, compiler, path)
            if diagram.tag:
                # Inlined extract_static_args
                static_args = None
                if all(isinstance(box, (computer.Data, computer.Copy, computer.Swap, computer.Merge, computer.Discard)) for box in diag.boxes):
                    static_args = tuple(box.value for box in diag.boxes if isinstance(box, computer.Data))
                
                args = static_args if static_args is not None else (diag,)
                atom = computer.Program(diagram.tag, computer.Language ** len(diagram.dom), computer.Language ** len(diagram.cod), args)
            else:
                atom = diag
        case yaml.Anchor():
            anchors = computer.RECURSION_REGISTRY.get().copy()
            compiled = compiler(diagram.inside, compiler, path)
            anchors[diagram.name] = compiled
            computer.RECURSION_REGISTRY.set(anchors)
            atom = computer.Program(diagram.name, computer.Language ** len(diagram.dom), computer.Language ** len(diagram.cod), (compiled,))
        case yaml.Alias():
            atom = computer.Program(diagram.name, computer.Language ** len(diagram.dom), computer.Language ** len(diagram.cod))

        # 3. Structural types from loader
        case loader.Swap():
            atom = computer.Swap(computer.Language ** len(diagram.dom[0:1]), computer.Language ** len(diagram.dom[1:2]))
        case loader.Copy():
            atom = computer.Copy(computer.Language ** len(diagram.dom), len(diagram.cod))
        case loader.Merge():
            atom = computer.Merge(computer.Language ** len(diagram.cod), len(diagram.dom))
        case loader.Discard():
            atom = computer.Discard(computer.Language ** len(diagram.dom))

        # 4. Generic Boxes (Atomic)
        case monoidal.Box():
            atom = closed.Id(computer.Language ** len(diagram.dom))

        # 5. Generic Diagrams (Composite)
        case symmetric.Diagram() | monoidal.Diagram():
            res = closed.Id(computer.Language ** len(diagram.dom))
            for box, offset in zip(diagram.boxes, diagram.offsets):
                if isinstance(box, (computer.Data, computer.Program, computer.Copy, computer.Merge, computer.Discard, computer.Swap, closed.Box)):
                    compiled = box
                elif isinstance(box, closed.Diagram):
                    compiled = box
                else:
                    compiled = compiler(box, compiler, path)
                
                left_id = closed.Id(res.cod[:offset])
                right_id = closed.Id(res.cod[offset + len(compiled.dom):])
                
                # AxiomError fix: ensure we stay in closed category and handle offsets correctly
                try:
                    layer = left_id.tensor(compiled, right_id)
                    res = res >> layer
                except Exception:
                    # Fallback or strict composition if tensor fails
                    res = res >> (closed.Id(res.cod[:offset]) @ compiled @ closed.Id(res.cod[offset+len(compiled.dom):]))
            
        case _:
            atom = closed.Id(closed.Ty())

    if atom is not None:
         res = (closed.Id(atom.dom) >> atom) if isinstance(atom, closed.Box) else atom
    
    if path is not None and __debug__ and not isinstance(diagram, (closed.Diagram, closed.Box)):
        from .files import diagram_draw
        diagram_draw(Path(path).with_suffix(".shell.yaml"), res)
    
    return res

SHELL_COMPILER.from_callable = from_callable
