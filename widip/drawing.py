import math
import sys
from pathlib import Path
from discopy import monoidal, closed
from discopy.closed import Ty

class ComplexityProfile:
    """
    A statistical model for characterizing DisCoPy diagram complexity.
    It maps logical diagram metrics (Width, Height, Box Count) into 
    visual layout parameters (Figsize, Fontsize, Proportions).
    """
    def __init__(self, rw, rh, rn, d_width, d_height):
        # rw: Max characters per wire (logical)
        # rh: Max lines per layer (logical)
        self.max_cpw = rw 
        self.max_lpl = rh
        self.rn = rn
        self.d_width = d_width   # DisCoPy grid width (max wires)
        self.d_height = d_height # DisCoPy grid depth (layers)
        
        self.density = rn / max(1, d_width * d_height)
        
    def get_layout_params(self):
        """
        Derives layout parameters using a non-linear scaling model.
        Goals:
        - Boxes should be wide enough for code.
        - Text should fit tightly in boxes.
        - Diagram should fill the SVG canvas with minimal margins.
        """
        # 1. Determine Target Font Size (points)
        # Using a slightly faster decay for font size to keep large diagrams manageable
        fsize = 120 / (math.pow(self.rn, 0.18))
        fsize = max(38, min(180, fsize))
        
        # 2. Derive Multipliers (Inches per DisCoPy Grid Unit)
        # pts per char (monospace): usually 0.6*fsize, but we use more for 'bold' look
        pts_per_char = fsize * 0.85 
        pts_per_line = fsize * 2.5 # Tighter vertical spacing for dense diagrams
        
        # Non-linear horizontal scaling: Wires shouldn't be pushed apart linearly 
        # by long text. We use a diminishing returns model.
        # Floor effective_cpw to ensure minimal box visibility
        effective_cpw = min(14, self.max_cpw) + 0.1 * max(0, self.max_cpw - 14)
        
        # Grid unit size in inches
        # We add a constant to ensure minimal size for spiders/empty units
        w_mult = (effective_cpw * pts_per_char) / 72.0 + 0.3
        h_mult = (self.max_lpl * pts_per_line) / 72.0 + 0.2
        
        # 3. Calculate Figsize (Inches)
        # We want zero margin. DisCoPy adds some internal axis padding.
        width = (self.d_width * w_mult)
        height = (self.d_height * h_mult)
        
        return {
            "figsize": (width, height),
            "fontsize": int(fsize),
            "textpad": (0.1, 0.2), # tight vertical centering
            "fontsize_types": max(14, int(fsize * 0.45))
        }

def get_recursive_stats(d, visited=None):
    """
    Finds the maximum content density required per grid unit.
    Returns (max_cpw, max_lpl, box_count)
    """
    if visited is None:
        visited = set()
        
    def is_bubble(obj):
        return isinstance(obj, monoidal.Bubble)

    max_cpw = 1.0 
    max_lpl = 1.0 
    box_count = 0
    
    def get_final_name(box):
        cls_name = type(box).__name__
        if cls_name == "Scalar":
             tag, val = getattr(box, "tag", ""), getattr(box, "value", "")
             if not tag and not val: return ""
             return f"{tag} {val}" if tag and val else (tag or val)
        if cls_name == "Alias": return f"*{box.name}"
        if cls_name == "Anchor": return f"&{box.name}"
        if cls_name == "Label": return box.name
        if cls_name == "Copy": return "Δ"
        if cls_name == "Merge": return "μ"
        if cls_name == "Discard": return "ε" if box.dom.name != "" else ""
        if cls_name == "Swap": return ""
        if cls_name == "Sequence": return f"[{getattr(box, 'tag', '')}]"
        if cls_name == "Mapping": return f"{{{getattr(box, 'tag', '')}}}"
        return str(getattr(box, "drawing_name", getattr(box, "name", "")))

    def walk(obj):
        nonlocal max_cpw, max_lpl, box_count
        obj_id = id(obj)
        name = get_final_name(obj)
        is_alias = isinstance(name, str) and name.startswith("*")

        if obj_id in visited:
            if is_alias:
                box_count += 30
                max_cpw = max(max_cpw, 10.0)
                max_lpl = max(max_lpl, 1.0)
            return
            
        visited.add(obj_id)

        if is_bubble(obj):
            walk(obj.inside)
            # Bubbles also have a title/name
            lines = name.split('\n')
            max_cpw = max(max_cpw, max(len(l) for l in lines) if lines else 0)
            return

        if hasattr(obj, "boxes") and obj.boxes and (len(obj.boxes) == 1 and obj.boxes[0] is obj):
             # Atomic Box
             lines = str(name).split('\n')
             l_w = max(1, max(len(l) for l in lines) if lines else 0)
             l_h = max(1, len(lines))
             
             wires = max(len(obj.dom), len(obj.cod)) if hasattr(obj, "dom") else 1
             cpw = l_w / max(1, wires)
             
             max_cpw = max(max_cpw, cpw)
             max_lpl = max(max_lpl, float(l_h))
             box_count += 30 if str(name).startswith("*") else 1
             return

        if hasattr(obj, "__iter__"):
             for layer in obj:
                  if hasattr(layer, "boxes"):
                      for b in layer.boxes: walk(b)
        elif hasattr(obj, "inside"): walk(obj.inside)
        elif hasattr(obj, "boxes"):
             for b in obj.boxes: walk(b)

    walk(d)
    return max_cpw, max_lpl, box_count

def diagram_draw(path: Path, fd):
    """
    Renders a DisCoPy diagram to SVG using the Complexity Attribution Model.
    """
    m_cpw, m_lpl, rn = get_recursive_stats(fd)
    
    # DisCoPy Grid units
    # fd.width is the max wires in any layer
    grid_w = getattr(fd, "width", len(fd.dom) if hasattr(fd, "dom") else 1)
    # len(fd) is number of layers
    grid_h = len(fd) if hasattr(fd, "__iter__") else 1
    
    profile = ComplexityProfile(m_cpw, m_lpl, rn, grid_w, grid_h)
    params = profile.get_layout_params()
    
    output_svg = str(path.with_suffix(".svg"))
    output_png = str(path.with_suffix(".png"))
    
    # Common draw params
    draw_params = {
        "aspect": "auto",
        "figsize": params["figsize"],
        "fontsize": params["fontsize"],
        "fontfamily": "monospace",
        "textpad": params["textpad"],
        "fontsize_types": params["fontsize_types"]
    }
    
    # standardization: prepare for drawing without leaking widip types
    # This prevents 'Mapping', 'Scalar' etc. from leaking into the SVG as class names.
    # It also handles the left-alignment padding without mutating the original diagram.

    def map_ob(ob):
        return monoidal.Ty(*[getattr(o, "name", str(o)) for o in ob.inside])

    def map_ar(box):
         cls_name = type(box).__name__
         
         # styling
         # use more premium, vibrant colors
         color = "#f0f0f0" # very light grey
         draw_as_spider = False
         draw_as_swap = False
         draw_as_bubble = False
         final_name = ""
         
         # Get the semantic name and identify spiders robustly
         name_str = str(getattr(box, "drawing_name", getattr(box, "name", "")))
         
         if cls_name == "Scalar" or name_str.startswith("Scalar"):
              tag, val = getattr(box, "tag", ""), getattr(box, "value", "")
              if not tag and not val:
                   final_name = ""
                   color = "#ffffff"
                   draw_as_spider = True
              else:
                   final_name = f"{tag} {val}" if tag and val else (tag or val)
                   color = "#ffffff"
         elif cls_name == "Alias" or name_str.startswith("*"):
                  final_name = f"*{getattr(box, 'name', name_str.lstrip('*'))}"
                  color = "#3498db" # vibrant blue
                  draw_as_spider = True
         elif cls_name == "Anchor" or name_str.startswith("&"):
                  final_name = f"&{getattr(box, 'name', name_str.lstrip('&'))}"
                  color = "#2980b9" # slightly darker vibrant blue
                  draw_as_spider = True
         elif cls_name == "Label":
                  final_name = name_str
                  color = "#ffffff"
         elif cls_name in ["Program", "Data"]:
                  final_name = name_str
                  color = "#ffffff"
         elif cls_name == "Copy" or name_str.startswith("Copy("):
                  final_name = "Δ"
                  color = "#2ecc71" # vibrant green
                  draw_as_spider = True
         elif cls_name == "Merge" or name_str.startswith("Merge("):
                  final_name = "μ"
                  color = "#27ae60" # darker vibrant green
                  draw_as_spider = True
         elif cls_name == "Discard" or name_str.startswith("Discard("):
                  if box.dom.name == "":
                       final_name = ""
                       color = "#ffffff"
                  else:
                       final_name = "ε"
                       color = "#e74c3c" # vibrant red
                  draw_as_spider = True
         elif cls_name == "Swap":
                  final_name = ""
                  color = "#f1c40f" # vibrant yellow
                  draw_as_swap = True
         elif cls_name in ["Sequence", "Mapping"]:
              tag = getattr(box, "tag", "")
              final_name = f"[{tag}]" if cls_name == "Sequence" else f"{{{tag}}}"
              if not tag: final_name = ""
              draw_as_bubble = True
              color = "#ffffff"
         else:
              final_name = name_str

         # Padded name for left-alignment
         lines = str(final_name).split('\n')
         # Map dom/cod
         dom = map_ob(box.dom)
         cod = map_ob(box.cod)
         wires = max(1, len(dom), len(cod))
         
         if draw_as_spider:
              # Spiders don't get padded, they stay at the cross-wire
              padded = final_name
         else:
              target_w = int(m_cpw * wires)
              padded = "\n".join([l.ljust(target_w) for l in lines])

         if draw_as_bubble or (isinstance(box, monoidal.Bubble) and not draw_as_spider):
              inside = standardize_recursive(box.inside) if hasattr(box, 'inside') else (monoidal.Box(padded, dom, cod))
              res = monoidal.Bubble(inside, dom, cod, drawing_name=padded)
         else:
              # Anchors/Aliases were inside bubbles, but we render them as spiders.
              res = monoidal.Box(padded, dom, cod, drawing_name=padded)

         res.color = color
         res.draw_as_spider = draw_as_spider
         res.draw_as_swap = draw_as_swap
         
         # DisCoPy styling tweaks
         if draw_as_spider:
              # Increase size significantly for GLA visibility
              res.shape = "circle"
              # DisCoPy uses nodesize for spiders
              res.nodesize = (1.5, 1.5) # Much larger for humans
         return res

    def standardize_recursive(diag):
        # Base case for Ty
        if not hasattr(diag, "boxes_and_offsets"):
             return diag 
        
        # Build a new monoidal Diagram from layers to avoid factory mismatch
        m_dom = map_ob(diag.dom)
        current_cod = m_dom
        inside = []
        for box, offset in diag.boxes_and_offsets:
            mapped_box = map_ar(box)
            # Reconstruct the layer manually
            left = monoidal.Id(current_cod[:offset])
            right = monoidal.Id(current_cod[offset + len(mapped_box.dom):])
            layer = monoidal.Layer(left, mapped_box, right)
            inside.append(layer)
            current_cod = layer.cod
            
        return monoidal.Diagram(inside, m_dom, current_cod)

    fd_draw = standardize_recursive(fd)
    
    # Save SVG
    fd_draw.draw(path=output_svg, **draw_params)
    
    # Save PNG for analysis
    try:
        fd_draw.draw(path=output_png, **draw_params)
    except Exception as e:
        print(f"Failed to save PNG: {e}", file=sys.stderr)
