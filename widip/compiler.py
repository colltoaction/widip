from .exec import Exec
from discopy import closed, monoidal, symmetric
from . import computer, yaml, loader
from pathlib import Path

def SHELL_COMPILER(diagram, compiler, path):
    atom = None
    res = None
    
    match diagram:
        # 1. Base cases: already compiled or explicit result types
        case closed.Diagram() | closed.Box():
            return diagram
            
        # 2. Specific YAML source types (Must come before generic Diagram/Box checks)
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
                res = res >> left_id.tensor(compiled, right_id)
            
        case _:
            atom = closed.Id(closed.Ty())

    if atom is not None:
         res = (closed.Id(atom.dom) >> atom) if isinstance(atom, closed.Box) else atom
    
    if path is not None and __debug__ and not isinstance(diagram, (closed.Diagram, closed.Box)):
        from .files import diagram_draw
        diagram_draw(Path(path).with_suffix(".shell.yaml"), res)
    
    return res
