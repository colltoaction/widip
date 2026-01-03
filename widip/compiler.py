from typing import Any, Union
from discopy import closed, monoidal, symmetric
from . import computer, yaml, loader
from pathlib import Path


def compile_scalar(diagram: yaml.Scalar, compiler_fn: Any, path: str | None) -> closed.Diagram:
    args = (diagram.value,) if diagram.value else ()
    if diagram.tag:
        return computer.Program(diagram.tag, computer.Language ** len(diagram.dom), computer.Language ** len(diagram.cod), args)
    return computer.Data(diagram.value, computer.Language ** len(diagram.dom), computer.Language ** len(diagram.cod))

def compile_container(diagram: Union[yaml.Sequence, yaml.Mapping], compiler_fn: Any, path: str | None) -> closed.Diagram:
    diag = compiler_fn(diagram.inside, compiler_fn, path)
    if diagram.tag:
        static_args = None
        if all(isinstance(box, (computer.Data, computer.Copy, computer.Swap, computer.Merge, computer.Discard)) for box in diag.boxes):
            static_args = tuple(box.value for box in diag.boxes if isinstance(box, computer.Data))
        
        args = static_args if static_args is not None else (diag,)
        return computer.Program(diagram.tag, computer.Language ** len(diagram.dom), computer.Language ** len(diagram.cod), args)
    return diag

def compile_anchor(diagram: yaml.Anchor, compiler_fn: Any, path: str | None) -> closed.Diagram:
    compiled = compiler_fn(diagram.inside, compiler_fn, path)
    computer.set_anchor(diagram.name, compiled)
    return computer.Program(diagram.name, computer.Language ** len(diagram.dom), computer.Language ** len(diagram.cod), (compiled,))

def compile_alias(diagram: yaml.Alias, compiler_fn: Any, path: str | None) -> closed.Diagram:
    return computer.Program(diagram.name, computer.Language ** len(diagram.dom), computer.Language ** len(diagram.cod))

def compile_structural(diagram: Any, compiler_fn: Any, path: str | None) -> closed.Diagram:
    match diagram:
        case loader.Swap():
            return computer.Swap(computer.Language ** len(diagram.dom[0:1]), computer.Language ** len(diagram.dom[1:2]))
        case loader.Copy():
            return computer.Copy(computer.Language ** len(diagram.dom), len(diagram.cod))
        case loader.Merge():
            return computer.Merge(computer.Language ** len(diagram.cod), len(diagram.dom))
        case loader.Discard():
            return computer.Discard(computer.Language ** len(diagram.dom))
        case _:
            raise TypeError(f"Unknown structural type: {type(diagram)}")

def SHELL_COMPILER(diagram: Any, compiler_fn: Any, path: str | None = None) -> closed.Diagram:
    """Compiles YAML diagrams into closed diagrams for execution."""
    def ar(box):
        match box:
            case _ if isinstance(box, (closed.Diagram, closed.Box)):
                return box
            case yaml.Scalar():
                return compile_scalar(box, compiler_fn, path)
            case yaml.Sequence() | yaml.Mapping():
                return compile_container(box, compiler_fn, path)
            case yaml.Anchor():
                return compile_anchor(box, compiler_fn, path)
            case yaml.Alias():
                return compile_alias(box, compiler_fn, path)
            case loader.Swap() | loader.Copy() | loader.Merge() | loader.Discard():
                return compile_structural(box, compiler_fn, path)
            case _ if isinstance(box, monoidal.Box):
                return closed.Id(computer.Language ** len(box.dom))
            case _:
                raise TypeError(f"Unknown box type: {type(box)}")

    cod = closed.Category()
    ob = lambda x: computer.Language ** len(x)
    
    match diagram:
        case closed.Diagram() | closed.Box():
            res = diagram
        case _ if callable(diagram) and not isinstance(diagram, (monoidal.Diagram, monoidal.Box, closed.Diagram)):
             res = computer.Program(getattr(diagram, '__name__', 'func'), 
                                     computer.Language, computer.Language, (diagram,))
        case yaml.Document():
             with computer.register_anchor("__document__", None):
                 res = compiler_fn(diagram.inside, compiler_fn, path)
        case yaml.Stream():
             res = compiler_fn(diagram.inside, compiler_fn, path)
        case _ if isinstance(diagram, (symmetric.Diagram, monoidal.Diagram)):
             res = closed.Functor(ob=ob, ar=ar, cod=cod)(diagram)
        case _:
             res = ar(diagram)

    if isinstance(res, (closed.Box, computer.Program, computer.Data)):
         res = closed.Id(res.dom) >> res
    
    if path is not None and __debug__ and not isinstance(diagram, (closed.Diagram, closed.Box)):
        from .drawing import diagram_draw
        diagram_draw(Path(path).with_suffix(".shell.yaml"), res)
    
    return res
