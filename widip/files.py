import sys
from pathlib import Path
from yaml import YAMLError

from discopy.closed import Ty, Diagram, Box, Functor
from discopy import monoidal

from nx_yaml import nx_compose_all
from .loader import incidences_to_diagram


def repl_read(stream):
    incidences = nx_compose_all(stream)
    return incidences_to_diagram(incidences)


def reload_diagram(path_str):
    print(f"reloading {path_str}", file=sys.stderr)
    try:
        fd = file_diagram(path_str)
        if hasattr(fd, "simplify"):
            fd = fd.simplify()
        diagram_draw(Path(path_str), fd)
    except YAMLError as e:
        print(e, file=sys.stderr)

def files_ar(ar: Box) -> Diagram:
    """Uses IO to read a file or dir with the box name as path"""
    if not ar.name.startswith("file://"):
        return ar

    try:
        return file_diagram(ar.name.lstrip("file://"))
    except IsADirectoryError:
        print("is a dir")
        return ar

def file_diagram(file_name) -> Diagram:
    path = Path(file_name)
    fd = repl_read(path.open())
    
    # Strip irrelevant Stream wrapper if present
    if isinstance(fd, monoidal.Bubble) and getattr(fd, "name", "") == "Stream":
         inner = fd.inside
         if hasattr(inner, "draw"): # It's a Diagram/Box
             fd = inner
         elif isinstance(inner, (list, tuple)) and len(inner) == 1:
             item = inner[0]
             # If it's a Layer, we can construct a Diagram from it
             if type(item).__name__ == "Layer":
                 # Ensure dom/cod are compatible Ty objects
                 # Force string conversion if needed, assuming simple types
                 # item.dom might be symmetric.Ty
                 # Reconstruct Diagram from Layer by tensoring boxes
                 if hasattr(item, "boxes") and item.boxes:
                     # Use the first box
                     fd = item.boxes[0]
                     # Tensor subsequent boxes
                     for b in item.boxes[1:]:
                         fd = fd @ b
                     # Note: layer dom/cod should match fd.dom/fd.cod
                 else:
                     # Empty layer? Identity.
                     # But we need types.
                     # Fallback to item if we can't reconstruct
                     fd = item 
             elif hasattr(item, "draw") or hasattr(item, "boxes"):
                 fd = item
             elif hasattr(item, "draw") or hasattr(item, "boxes"):
                 fd = item
         # If tuple with multiple items, we could construct Diagram if we knew dom/cod.
         # For now, sticking to single-layer unwrap which handles most cases like countdown.
    
    return fd

def get_recursive_stats(d, visited=None):
    """Recursively calculate effective width, height, and box count of a diagram."""
    if visited is None:
        visited = set()
        
    # Prevent infinite recursion on cyclic/recursive structures
    d_id = id(d)
    if d_id in visited:
        # Heuristic: returning a "phantom" size for recursive calls
        return 5.0, 5.0, 30
    visited.add(d_id)

    # Bubbles (Stream, Sequence, Mapping, etc.) wrap a diagram in .inside
    # We must recurse into them.
    if isinstance(d, monoidal.Bubble):
        return get_recursive_stats(d.inside, visited)

    if isinstance(d, (list, tuple)):
        child_stats = [get_recursive_stats(item, visited) for item in d]
        if not child_stats:
            return 1.0, 1.0, 1
        
        widths = [s[0] for s in child_stats]
        heights = [s[1] for s in child_stats]
        counts = [s[2] for s in child_stats]
        
        return max(widths), sum(heights), sum(counts)

    # Helper to check for Alias
    def is_alias(obj):
        dname = getattr(obj, "drawing_name", getattr(obj, "name", ""))
        return dname.startswith("*")

    if not hasattr(d, "boxes") or not d.boxes:
        # Scalar or empty (or unexpected structure)
        # Heuristic for text width: ~0.35 units per character
        name_len = len(getattr(d, "drawing_name", getattr(d, "name", "")))
        text_w = max(1.0, name_len * 0.35)
        
        # Consider wires (dom/cod)
        wires = max(len(d.dom), len(d.cod)) if hasattr(d, "dom") else 0
        eff_w = max(text_w, wires * 0.5)
        
        count = 1
        if is_alias(d):
            count = 30
        
        return eff_w, 1.0, count
    
    # It is a composite Diagram (or a Box that exposes boxes?)
    boxes = d.boxes
    
    if len(boxes) == 1 and boxes[0] is d:
         # Primitive box
         name_len = len(getattr(d, "drawing_name", getattr(d, "name", "")))
         text_w = max(1.0, name_len * 0.35)
         wires = max(len(d.dom), len(d.cod)) if hasattr(d, "dom") else 0
         eff_w = max(text_w, wires * 0.5)
         
         count = 1
         if is_alias(d):
             count = 30
             
         return eff_w, 1.0, count

    # Composite Diagram: Calculate stats for all children
    child_stats = []
    for box in boxes:
        child_stats.append(get_recursive_stats(box, visited))
            
    if not child_stats:
        return 1.0, 1.0, 1
        
    # Compute totals
    total_w = sum(s[0] for s in child_stats)
    total_h = sum(s[1] for s in child_stats)
    total_count = sum(s[2] for s in child_stats)
    
    # Structural approximation
    avg_w = total_w / len(child_stats)
    avg_h = total_h / len(child_stats)
    
    # Add padding for container (bubbles usually add visual padding)
    # 3.0 units padding balances box size vs diagram size
    padding = 3.0 if hasattr(d, "boxes") else 0.0
    
    d_width = d.width if hasattr(d, "width") else (len(d.dom) if hasattr(d, "dom") else 1)
    d_depth = len(d) if hasattr(d, "__len__") and not hasattr(d, "boxes") else 1
    
    if type(d).__name__ == "Layer":
        d_depth = 1
        # Layer width via dom
        d_width = len(d.dom) if hasattr(d, "dom") else 1
    elif hasattr(d, "__len__"):
        d_depth = len(d)
        
    eff_w = (max(1, d_width) * avg_w) + padding
    eff_h = (d_depth * avg_h) + padding
    
    return eff_w, eff_h, total_count

def diagram_draw(path, fd):
    # Calculate figsize based on recursive diagram dimensions and density
    rw, rh, rn = get_recursive_stats(fd)
    
    # Dynamic Multiplier based on complexity (box count)
    # Scaled down exponent to avoid exploding medium diagrams like shell
    rn_pow = rn ** 1.55
    
    w_mult = min(50.0, 0.4 + rn_pow * 0.005)
    h_mult = min(60.0, 0.4 + rn_pow * 0.007)
    
    width = max(3, 1 + rw * w_mult)
    height = max(2, 1 + rh * h_mult)
    
    # Text pad logic
    area = width * height
    density = rn / max(1, area)
    
    pad = max(0.05, min(0.3, 0.25 / (density + 0.1))) 
    
    # Font size
    # Average multiplier dictates "zoom"
    avg_mult = (w_mult + h_mult) / 2
    fsize = max(14, min(48, 12 + avg_mult * 4))

    # SVG output - vector format, scales perfectly
    fd.draw(path=str(path.with_suffix(".svg")),
            aspect="auto",
            figsize=(width, height),
            textpad=(pad, pad),
            fontsize=fsize,
            fontsize_types=int(fsize * 0.7))

files_f = Functor(lambda x: Ty(""), files_ar)
