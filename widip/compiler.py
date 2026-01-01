import sys
from discopy import closed, monoidal

from .computer import *
from .yaml import *


def compose_loose(f, g):
    if f.cod == g.dom:
        return f >> g
        
    # Broadcasting check: 1 output -> N inputs
    # Assuming types are IO-like and fungible?
    # Strictly checking counts.
    if len(f.cod) == 1 and len(g.dom) > 1:
        # Insert Copy
        # We assume f.cod[0] is compatible with all g.dom inputs (IO)
        return f >> Copy(f.cod, len(g.dom)) >> g
        
    return f >> Cast(f.cod, g.dom) >> g


def compile_ar(ar):
    
    dom = closed.Ty() # Placeholder
    cod = closed.Ty()
    
    from .yaml import Mapping as YamlMapping, Sequence as YamlSequence

    if isinstance(ar, YamlMapping):
        inner = ar.args[0]
        boxes = inner.boxes if hasattr(inner, 'boxes') else inner if isinstance(inner, (list, tuple)) else [inner]
        
        if not boxes:
            return closed.Id(closed.Ty())
            
        compiled_items = []
        for box in boxes:
            c = compile_diagram(box)
            if not isinstance(c, closed.Diagram): c = closed.Id(c.dom) >> c
            compiled_items.append(c)
            
        res = compiled_items[0]
        for item in compiled_items[1:]:
            res = res @ item
        return res

    if isinstance(ar, Node):
        p_dom = closed.Ty("IO")
        # If Node has args (from loader process_mapping/sequence)
        # compile args and inject
        if hasattr(ar, 'args') and ar.args:
             args_compiled = compile_diagram(ar.args)
             p_dom = p_dom @ args_compiled.cod
             
             # Guard against monoidal types
             # ...
             
             p = Program(ar.name, dom=p_dom, cod=closed.Ty("IO")).uncurry()
             return (closed.Id(closed.Ty("IO")) @ args_compiled) >> p
             
        return Program(ar.name, dom=p_dom, cod=p_dom).uncurry()

    if isinstance(ar, Scalar):
        # Ensure implicit IO is part of domain for all shell programs/execs
        # Even scalars from Key/Val should treat IO as the main wire.
        # We assume one main IO stream.
        io_dom = closed.Ty("IO") # Language
        # ar.dom from loader might be empty or IO. We want to coerce to IO flow.
        
        # If ar.tag is present, it is a Program.
        if ar.tag == "exec":
             return Exec(io_dom, io_dom)

        if ar.tag:
             # Program
             # We want dom = IO (stdin) + Args.
             # If value is present, treat as argument.
             
             p_dom = io_dom
             
             if ar.value:
                  # Inject argument constant
                  val_ty = closed.Ty(ar.value)
                  p_dom = p_dom @ val_ty
                  # Wiring: Input(IO) -> (Input(IO) @ Data(Val))
                  arg_box = closed.Id(io_dom) @ Data(closed.Ty(), val_ty)
             else:
                  arg_box = closed.Id(io_dom)
            
             # Create Program consuming inputs + args
             # cod is IO (Language)
             p = Program(ar.tag, dom=p_dom, cod=io_dom).uncurry()
             
             # Diagram: Input -> (Input @ Arg) -> Eval -> Output
             return arg_box >> p
             
        # If no tag (Data/Constant scalar potentially)
        # But if it's acting as a source/sink?
        # "wc -c". "-c" is scalar. Loader produces Scalar with no tag?
        # No, loader produced Scalar(wc, -c).
        # What about `tail -2`? Scalar(tail, -2).
        if not ar.tag and not ar.value:
             return closed.Id(io_dom)
             
        return Data(closed.Ty(), closed.Ty(ar.value))

    if isinstance(ar, YamlSequence):
        inner = ar.args[0]
        boxes = inner.boxes if hasattr(inner, 'boxes') else inner if isinstance(inner, (list, tuple)) else [inner]
        
        if not boxes:
            return closed.Id(closed.Ty("IO"))
        
        # Helper to ensure Diagram
        def ensure_diagram(b):
            c = compile_diagram(b)
            if not isinstance(c, closed.Diagram):
                 # c is compiled box (from Computation). It is closed Box/Diagram.
                 # If it has dom IO, we wrap it.
                 c = closed.Id(c.dom) >> c
            return c
            
        res = ensure_diagram(boxes[0])
        
        for b in boxes[1:]:
            c = ensure_diagram(b)
            
            # Broadcasting logic for key-value pair (n=2 implied if we are in this block and splitting items?)
            # Actually ar.n is accessible here.
            if ar.n == 2 and len(res.cod) == 1 and len(c.dom) > 1:
                # Assuming simple broadcasting of the single output to all inputs
                # We need to ensure types match (e.g. all are IO)
                broadcaster = Copy(res.cod, len(c.dom))
                res = res >> broadcaster >> c
            else:
                res = compose_loose(res, c)
        return res


    if isinstance(ar, Alias):
        d = closed.Ty("IO")
        # return Data(dom, cod) >> Copy(cod, 2) ...
        # If Alias is variable reference.
        # Currently just creating structural wires.
        return Data(closed.Ty(), d) >> Copy(d, 2) >> closed.Id(d) @ Discard(d)

    if isinstance(ar, Anchor):
        d = closed.Ty("IO")
        return Copy(d, 2) >> closed.Id(d) @ Discard(d)

    if isinstance(ar, monoidal.Diagram):
        return compile_diagram(ar)
        
    from discopy.monoidal import Layer
    if isinstance(ar, Layer):
        # Layer -> Id(left) @ compile(box) @ Id(right)
        # Infer left/right from offset
        
        box, offset = ar.boxes_and_offsets[0]
        
        def convert_ty(t):
            # Convert monoidal.Ty to closed.Ty
            if not t: return closed.Ty()
            return closed.Ty(*t.objects)
            
        left_ty = ar.dom[:offset]
        right_ty = ar.dom[offset + len(box.dom):]
        
        l = convert_ty(left_ty)
        r = convert_ty(right_ty)
        center = compile_ar(box)
        
        if not isinstance(center, closed.Diagram):
             center = closed.Id(center.dom) >> center
             
        return closed.Id(l) @ center @ closed.Id(r)
    
    if hasattr(ar, "dom") and hasattr(ar, "cod"):
        return ar
    
    return ar

def compile_diagram(diagram):
    if isinstance(diagram, monoidal.Diagram):
        boxes = diagram.boxes
        if not boxes:
            return closed.Id(closed.Ty("IO"))
        # Default behavior for Diagram: Sequence/Pipeline composition
        res = compile_ar(boxes[0])
        for b in boxes[1:]:
             res = compose_loose(res, compile_ar(b))
        return res
    if isinstance(diagram, (list, tuple)):
         # Should not happen if calling logic is correct
         if not diagram: return closed.Id(closed.Ty("IO"))
         res = compile_ar(diagram[0])
         for b in diagram[1:]:
             res = res @ compile_ar(b)
         return res
         
    return compile_ar(diagram)

SHELL_COMPILER = compile_diagram


def compile_shell_program(diagram):
    """
    close input parameters (constants)
    drop outputs matching input parameters
    all boxes are io->[io]"""
    diagram = SHELL_COMPILER(diagram)
    return diagram
