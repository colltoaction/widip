from __future__ import annotations
from .exec import Exec
from discopy import closed, monoidal, symmetric
from . import computer, yaml, loader
from pathlib import Path


def compile_scalar(diagram, compiler, path):
    args = (diagram.value,) if diagram.value else ()
    if diagram.tag:
        return computer.Program(diagram.tag, computer.Language ** len(diagram.dom), computer.Language ** len(diagram.cod), args)
    return computer.Data(diagram.value, computer.Language ** len(diagram.dom), computer.Language ** len(diagram.cod))

def compile_container(diagram, compiler, path):
    diag = compiler(diagram.inside, compiler, path)
    if diagram.tag:
        static_args = None
        if all(isinstance(box, (computer.Data, computer.Copy, computer.Swap, computer.Merge, computer.Discard)) for box in diag.boxes):
            static_args = tuple(box.value for box in diag.boxes if isinstance(box, computer.Data))
        
        args = static_args if static_args is not None else (diag,)
        return computer.Program(diagram.tag, computer.Language ** len(diagram.dom), computer.Language ** len(diagram.cod), args)
    return diag

def compile_anchor(diagram, compiler, path):
    compiled = compiler(diagram.inside, compiler, path)
    computer.set_anchor(diagram.name, compiled)
    return computer.Program(diagram.name, computer.Language ** len(diagram.dom), computer.Language ** len(diagram.cod), (compiled,))

def compile_alias(diagram, compiler, path):
    return computer.Program(diagram.name, computer.Language ** len(diagram.dom), computer.Language ** len(diagram.cod))

def compile_structural(diagram, compiler, path):
    match diagram:
        case loader.Swap():
            return computer.Swap(computer.Language ** len(diagram.dom[0:1]), computer.Language ** len(diagram.dom[1:2]))
        case loader.Copy():
            return computer.Copy(computer.Language ** len(diagram.dom), len(diagram.cod))
        case loader.Merge():
            return computer.Merge(computer.Language ** len(diagram.cod), len(diagram.dom))
        case loader.Discard():
            return computer.Discard(computer.Language ** len(diagram.dom))

def compile_diagram(diagram, compiler, path):
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
        
        try:
            layer = left_id.tensor(compiled, right_id)
            res = res >> layer
        except Exception:
            res = res >> (closed.Id(res.cod[:offset]) @ compiled @ closed.Id(res.cod[offset+len(compiled.dom):]))
    return res

def SHELL_COMPILER(diagram, compiler, path):
    res = None
    
    match diagram:
        case closed.Diagram() | closed.Box():
            res = diagram
        case _ if callable(diagram) and not isinstance(diagram, (monoidal.Diagram, monoidal.Box)):
             res = computer.Program(getattr(diagram, '__name__', 'func'), 
                                     computer.Language, computer.Language, (diagram,))
        case yaml.Scalar(): res = compile_scalar(diagram, compiler, path)
        case yaml.Sequence() | yaml.Mapping(): res = compile_container(diagram, compiler, path)
        case yaml.Anchor(): res = compile_anchor(diagram, compiler, path)
        case yaml.Alias(): res = compile_alias(diagram, compiler, path)
        case loader.Swap() | loader.Copy() | loader.Merge() | loader.Discard(): res = compile_structural(diagram, compiler, path)
        case monoidal.Box(): res = closed.Id(computer.Language ** len(diagram.dom))
        case symmetric.Diagram() | monoidal.Diagram(): res = compile_diagram(diagram, compiler, path)
        case _: res = closed.Id(closed.Ty())

    if isinstance(res, closed.Box):
         res = closed.Id(res.dom) >> res
    
    if path is not None and __debug__ and not isinstance(diagram, (closed.Diagram, closed.Box)):
        from .drawing import diagram_draw
        diagram_draw(Path(path).with_suffix(".shell.yaml"), res)
    
    return res
