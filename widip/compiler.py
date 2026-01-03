from discopy import closed, monoidal, symmetric
from . import computer, yaml, loader
from pathlib import Path

def extract_static_args(diag):
    if all(isinstance(box, (computer.Data, computer.Copy, computer.Swap, computer.Merge, computer.Discard)) for box in diag.boxes):
        return tuple(box.value for box in diag.boxes if isinstance(box, computer.Data))
    return None

def map_ob(ob):
    return computer.Language ** len(ob)

def compile_yaml_collection(ar, compiler, path):
    diag = compiler(ar.inside, compiler, path)
    if ar.tag:
        static_args = extract_static_args(diag)
        args = static_args if static_args is not None else (diag,)
        return computer.Program(ar.tag, map_ob(ar.dom), map_ob(ar.cod), args)
    return diag

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
            atom = computer.Program(diagram.tag, map_ob(diagram.dom), map_ob(diagram.cod), args) if diagram.tag else \
                   computer.Data(diagram.value, map_ob(diagram.dom), map_ob(diagram.cod))
        case yaml.Sequence() | yaml.Mapping():
            atom = compile_yaml_collection(diagram, compiler, path)
        case yaml.Anchor():
            anchors = computer.RECURSION_REGISTRY.get().copy()
            compiled = compiler(diagram.inside, compiler, path)
            anchors[diagram.name] = compiled
            computer.RECURSION_REGISTRY.set(anchors)
            atom = computer.Program(diagram.name, map_ob(diagram.dom), map_ob(diagram.cod), (compiled,))
        case yaml.Alias():
            atom = computer.Program(diagram.name, map_ob(diagram.dom), map_ob(diagram.cod))

        # 3. Structural types from loader
        case loader.Swap():
            atom = computer.Swap(map_ob(diagram.dom[0:1]), map_ob(diagram.dom[1:2]))
        case loader.Copy():
            atom = computer.Copy(map_ob(diagram.dom), len(diagram.cod))
        case loader.Merge():
            atom = computer.Merge(map_ob(diagram.cod), len(diagram.dom))
        case loader.Discard():
            atom = computer.Discard(map_ob(diagram.dom))

        # 4. Generic Boxes (Atomic)
        # MUST come before monoidal.Diagram because Box inherits from Diagram
        case monoidal.Box():
            # Default for generic boxes: Identity or Opaque
            atom = closed.Id(map_ob(diagram.dom))

        # 5. Generic Diagrams (Composite)
        case symmetric.Diagram() | monoidal.Diagram():
            # Revert to iterative construction for safety and correctness
            res = closed.Id(map_ob(diagram.dom))
            for box, offset in zip(diagram.boxes, diagram.offsets):
                # If box is already compiled, use it
                if isinstance(box, (computer.Data, computer.Program, computer.Copy, computer.Merge, computer.Discard, computer.Swap, closed.Box)):
                    compiled = box
                # If it's a closed.Diagram, assume it's good (it matched case 1 potentially, but here it's inside another diagram)
                elif isinstance(box, closed.Diagram):
                    compiled = box
                else:
                    compiled = compiler(box, compiler, path)
                
                # Compose safely
                res >>= (closed.Id(res.cod[:offset]) @ compiled @ closed.Id(res.cod[offset + len(compiled.dom):]))
            
        case _:
            # Fallback
            atom = closed.Id(closed.Ty())

    if atom is not None:
         res = (closed.Id(atom.dom) >> atom) if isinstance(atom, closed.Box) else atom
    
    if path is not None and __debug__ and not isinstance(diagram, (closed.Diagram, closed.Box)):
        from .files import diagram_draw
        diagram_draw(Path(path).with_suffix(".shell.yaml"), res)
    
    return res
