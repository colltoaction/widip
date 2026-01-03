import sys
from pathlib import Path
from yaml import YAMLError

from discopy.closed import Ty, Diagram, Box, Functor

from nx_yaml import nx_compose_all
from .loader import incidences_to_diagram


def repl_read(stream):
    incidences = nx_compose_all(stream)
    return incidences_to_diagram(incidences)


def reload_diagram(path_str):
    print(f"reloading {path_str}", file=sys.stderr)
    try:
        fd = file_diagram(path_str).simplify()
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
    return fd

def get_recursive_stats(d):
    """Recursively calculate effective width, height, and box count of a diagram."""
    if not hasattr(d, "boxes") or not d.boxes:
        # Scalar or empty
        # Heuristic for text width: ~0.35 units per character
        name_len = len(getattr(d, "drawing_name", getattr(d, "name", "")))
        text_w = max(1.0, name_len * 0.35)
        return text_w, 1.0, 1
    
    # Calculate stats for all children
    child_stats = []
    for box in d.boxes:
        if hasattr(box, "inside"):
            child_stats.append(get_recursive_stats(box.inside))
        else:
            # Simple box
            name_len = len(getattr(box, "drawing_name", getattr(box, "name", "")))
            text_w = max(1.0, name_len * 0.35)
            child_stats.append((text_w, 1.0, 1))
            
    if not child_stats:
        return 1.0, 1.0, 1
        
    # Compute averages
    avg_w = sum(s[0] for s in child_stats) / len(child_stats)
    avg_h = sum(s[1] for s in child_stats) / len(child_stats)
    total_count = sum(s[2] for s in child_stats)
    
    # Structural approximation
    # Width ~ Parallelism (d.width) * Average Component Width
    # Height ~ Depth (len(d)) * Average Component Height
    
    # Add padding for container (bubbles usually add visual padding)
    # 3.0 units padding balances box size vs diagram size
    padding = 3.0 if hasattr(d, "boxes") else 0.0
    
    eff_w = (max(1, d.width) * avg_w) + padding
    eff_h = (len(d) * avg_h) + padding
    
    return eff_w, eff_h, total_count

def diagram_draw(path, fd):
    # Calculate figsize based on recursive diagram dimensions and density
    rw, rh, rn = get_recursive_stats(fd)
    
    # Dynamic Multiplier based on complexity (box count)
    # User feedback: "countdown seems to be much more complex than you anticipate"
    # Action: Drastically increase impact of complexity (rn) on scaling
    
    # Steeper slopes to separate simple vs complex
    # Quadratic scaling (power 2.0) to decimate shell size and inflate countdown
    # rn=5 (shell) -> 25. rn=60 (countdown) -> 3600. Ratio ~144x.
    
    rn_pow = rn ** 2.0
    # Small base (0.3) ensures shell stays tiny
    w_mult = min(40.0, 0.3 + rn_pow * 0.005)
    h_mult = min(50.0, 0.3 + rn_pow * 0.01)
    
    width = max(3, 1 + rw * w_mult)
    height = max(2, 1 + rh * h_mult)
    
    # Calculate density using actual box count
    # rn boxes in width*height area
    density = rn / (width * height)
    
    # Inverse padding: High density -> Low padding
    # Density approx 0.5-2.0.
    # If density 1.0 -> pad 0.1
    # Cap padding lower to help text fit
    pad = max(0.05, min(0.2, 0.2 / (density + 0.1)))
    
    # Dynamic fontsize SCALED by average multiplier
    # Scales text with the "zoom level"
    # Base font 16 (Large)
    avg_mult = (w_mult + h_mult) / 2
    fsize = 16 * avg_mult

    # SVG output - vector format, scales perfectly
    fd.draw(path=str(path.with_suffix(".svg")),
            aspect="auto",
            figsize=(width, height),
            textpad=(pad, pad),
            fontsize=fsize,
            fontsize_types=int(fsize * 0.7))

files_f = Functor(lambda x: Ty(""), files_ar)
