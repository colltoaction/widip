from __future__ import annotations
from typing import Any
from discopy import closed, symmetric, frobenius
from .representation import Scalar, Sequence, Mapping, Anchor, Alias, Document, Stream
from ..core import Language, Copy, Merge, Discard, Program, Data, Titi

# Create diagram instances for copy, merge, discard
copy = Copy(Language, 2) >> closed.Id(Language ** 2)
merge = Merge(Language, 2) >> closed.Id(Language)
discard = Discard(Language) >> closed.Id(closed.Ty())

# Ensure Language is the base closed.Ty
L = Language

def make_copy(n):
    if n <= 1: return closed.Id(Language ** n)
    return Copy(Language, n) >> closed.Id(Language ** n)

def make_merge(n):
    if n <= 1: return closed.Id(Language ** n)
    return Merge(Language, n) >> closed.Id(Language)

# Helper to extract static arguments
def extract_args(box):
    """Recursively extract static arguments from boxes, following representation kinds."""
    if hasattr(box, 'kind') and box.kind == "Scalar":
        val = getattr(box, 'value', None)
        if not val: return ()
        return (str(val),)
    
    nested = getattr(box, 'nested', None)
    if nested is not None: 
        args = []
        # If nested is a diagram, iterate its boxes
        if hasattr(nested, 'boxes'):
            for b in nested.boxes:
                if hasattr(b, 'kind'):
                    args.extend(extract_args(b))
        # If nested is a single box or object
        elif hasattr(nested, 'kind'):
             args.extend(extract_args(nested))
             
        return tuple(args)
    return ()

def construct_box(box) -> closed.Diagram:
    import computer.yaml
    
    tag = getattr(box, 'tag', None)
    value = getattr(box, 'value', None)
    nested = getattr(box, 'nested', None)
    name = getattr(box, 'name', None)
    kind = getattr(box, 'kind', name)
    anchor_name = getattr(box, 'anchor_name', None)

    # 1. Handle Titi Special Case
    if kind == "Titi" or tag == "titi":
        inside = computer.yaml.construct_functor(nested)
        start = Titi.read_stdin
        # Match inside domain
        n_in = len(inside.dom)
        if n_in == 0:
            start = start >> Discard()
        elif n_in > 1:
            start = start >> make_copy(n_in)
        
        # Match inside codomain to printer
        n_out = len(inside.cod)
        if n_out == 0:
            core = start >> inside
        else:
            if n_out > 1:
                inside = inside >> make_merge(n_out)
            core = start >> inside >> Titi.printer
        
        # Ensure core codomain is Ty() before passing to final Data box
        if len(core.cod) > 0:
            core = core >> Discard(core.cod)
        
        return core >> Data("")

    # 2. Handle Anchor
    if kind == "Anchor" or (kind and kind.startswith("Anchor(")):
        anchor_name = anchor_name or name.split("(")[1].split(")")[0]
        inside = computer.yaml.construct_functor(nested)
        return Program("anchor", (anchor_name, inside))

    # 3. Handle Alias
    if kind == "Alias":
        return Program("alias", (anchor_name,))

    # 4. Handle Scalar (Leaf)
    if kind == "Scalar":
        if tag:
            if tag == "id": return closed.Id(Language)
            if tag == "xargs": return Program("xargs", (value,))
            if tag.lower() == "data": return Data(value)
            if tag.lower() == "program": return Program(value)
            # Handle Partial specially
            if tag == "Partial":
                 from computer import Partial
                 return Partial(value)
            # Fall through for other tags
        else:
            if value is None or value == "":
                return closed.Id(Language)
            return Data(value)

    # Special: Treat untagged sequences as accumulative pipelines (print taps)
    is_seq = kind == "Sequence" and not tag
    has_inside = hasattr(nested, 'inside') or isinstance(nested, list)
    if is_seq and has_inside:
          items = nested.inside if hasattr(nested, 'inside') else nested
          return sequential_compose(items)
    
    if kind == "Stream":
          items = nested.inside if hasattr(nested, 'inside') else nested
          return Program("stream", (items,))

    if nested is None:
         inside = closed.Id(Language)
    else:
         inside = computer.yaml.construct_functor(nested)

    
    if kind == "Mapping" and not tag:
        # Raw tensor representation for untagged mappings
        return inside

    # Trace back algebraic ops
    if kind == "Δ": return copy
    if kind == "μ": return merge
    if kind == "ε": return discard

    if tag and kind not in ["Titi"]:
        if tag == "seq": return inside
        
        # --- Supercompilation Tags ---
        if tag == "specializer":
            from ..super_extended import specializer_box
            return specializer_box >> closed.Id(Language)
        
        if tag == "futamura1":
            from ..super_extended import futamura_1
            # Extract interpreter and program from nested
            if hasattr(nested, 'inside') and len(nested.inside) >= 2:
                interp = computer.yaml.construct_functor(nested.inside[0])
                prog = computer.yaml.construct_functor(nested.inside[1])
                return futamura_1(interp, prog)
            return inside
        
        if tag == "futamura2":
            from ..super_extended import futamura_2
            if hasattr(nested, 'inside') and len(nested.inside) >= 2:
                interp = computer.yaml.construct_functor(nested.inside[0])
                spec = computer.yaml.construct_functor(nested.inside[1])
                return futamura_2(interp, spec)
            return inside
        
        if tag == "futamura3":
            from ..super_extended import futamura_3
            if hasattr(nested, 'inside') and len(nested.inside) >= 1:
                spec = computer.yaml.construct_functor(nested.inside[0])
                return futamura_3(spec)
            return inside
        
        if tag == "supercompile":
            from ..super_extended import Supercompiler
            sc = Supercompiler()
            return sc.supercompile(inside)
        
        # --- Hypercomputation Tags ---
        if tag == "ackermann":
            from ..hyper_extended import ackermann_box
            res = ackermann_box >> closed.Id(Language)
            if inside is not None:
                return inside >> res
            return res
        
        if tag == "fast_growing":
            from ..hyper_extended import fast_growing_box
            res = fast_growing_box >> closed.Id(Language)
            if inside is not None:
                return inside >> res
            return res
        
        if tag == "busy_beaver":
            from ..hyper_extended import busy_beaver_box
            res = busy_beaver_box >> closed.Id(Language)
            if inside is not None:
                return inside >> res
            return res
        
        if tag == "goodstein":
            from ..hyper_extended import goodstein_box
            res = goodstein_box >> closed.Id(Language)
            if inside is not None:
                return inside >> res
            return res
        
        if tag == "omega_iterate":
            from ..hyper_extended import iterate_omega
            return iterate_omega(inside)
        
        if tag == "diagonal":
            from ..hyper_extended import diagonal
            return diagonal(inside)
        
        if tag == "transfinite":
            from ..hyper_extended import transfinite_box
            res = transfinite_box >> closed.Id(Language)
            if inside is not None:
                return inside >> res
            return res
        
        if tag == "omega":
            from ..hyper_extended import OrdinalNotation
            omega = OrdinalNotation.omega()
            return Data(str(omega)) >> closed.Id(Language)
        
        if tag == "epsilon_0":
            from ..hyper_extended import OrdinalNotation
            eps0 = OrdinalNotation.epsilon_0()
            return Data(str(eps0)) >> closed.Id(Language)
        
        if tag == "choice":
            # Conditional choice between branches
            if hasattr(nested, 'inside') and len(nested.inside) >= 2:
                 branch1 = computer.yaml.construct_functor(nested.inside[0])
                 branch2 = computer.yaml.construct_functor(nested.inside[1])
                 return Program("choice", (branch1, branch2))
            return inside
        
        if tag == "mapping":
            # Explicit tensor product
            return inside
            
        if tag == "seq":
            # Explicit sequential composition
            items = nested.inside if hasattr(nested, 'inside') else nested
            return sequential_compose(items)
        
        # --- Parser Integration Tags ---
        if tag == "parse_yaml":
            from ..parser_bridge import YAMLParserBridge
            parser = YAMLParserBridge()
            # Extract source from nested
            source_val = value or ""
            if hasattr(nested, 'inside'):
                # Try to extract source from nested structure
                pass
            return parser.parse(source_val)
        
        if tag == "lex":
            # Run lex on the specified file
            args = extract_args(box)
            return Program("lex", args)
        
        if tag == "yacc":
            # Run yacc on the specified file
            args = extract_args(box)
            return Program("yacc", args)
        
        if tag == "cc":
            # Run C compiler
            args = extract_args(box)
            return Program("cc", args)

        if tag.lower() == "data":
            # Extract scalar value from inside
            # inside is typically Data(val) already if derived from Scalar
            # If kind="Tagged", nested=Scalar("val") -> inside=Data("val")
            # So just return inside.
            return inside
        
        if tag.lower() == "program":
            # If nested is already a Program box (unwrap)
            return inside

        # Default: create Program with tag and args
        args = extract_args(box)
        return Program(tag, args)

    return inside
def sequential_compose(items: list) -> closed.Diagram:
    """
    Helper to compose a list of items with 'Accumulative Tap' behavior.
    If multiple items produce output (codomain is Language), they are
    automatically merged (μ) so all outputs are preserved.
    """
    import computer
    from ..core import Language, Discard, make_copy, make_merge, Copy, Merge
    from discopy import closed
    
    res = None
    # Edge case: If 1 item and it's a Program, just return it directly (unwrap)
    if len(items) == 1:
        return computer.yaml.construct_functor(items[0])

    for layer in items:
        layer_diag = computer.yaml.construct_functor(layer)
        if res is None:
            res = layer_diag
        else:
            # Robust Accumulative Composition
            n_res = len(res.cod)
            n_layer = len(layer_diag.dom)
            
            # If both have Language cod/dom, we can pipe OR tap
            # For "Accumulative Tap", we want to preserve previous output
            # and ALSO run the next one.
            
            # If both have Language cod/dom AND matching output arity, use Accumulative Tap
            n_layer_cod = len(layer_diag.cod)
            if n_res == 1 and n_layer == 1 and n_layer_cod == 1:
                 # Shared input + Parallel output merged
                 res = make_copy(2) >> (res @ layer_diag) >> make_merge(2)
            elif n_res == n_layer:
                res = res >> layer_diag
            elif n_layer == 0:
                # Parallel composition: next one is a source
                res = res @ layer_diag
            elif n_res == 0:
                # Sequence: previous produced nothing, next starts fresh
                res = res >> layer_diag
            elif n_res < n_layer:
                # fan out
                if n_res == 1:
                    res = res >> make_copy(n_layer) >> layer_diag
                else: res = res >> layer_diag
            elif n_res > n_layer:
                # merge or discard
                if n_layer == 1:
                    res = res >> make_merge(n_res) >> layer_diag
                else:
                    extra = n_res - n_layer
                    res = res >> (closed.Id(Language ** n_layer) @ Discard(Language ** extra)) >> layer_diag
    return res or closed.Id(Language)
