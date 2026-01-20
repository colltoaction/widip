import math, sys
from pathlib import Path
from discopy import monoidal, closed

class ComplexityProfile:
    def __init__(self, rw, rh, rn, d_width, d_height):
        self.max_cpw, self.max_lpl, self.rn, self.d_width, self.d_height = rw, rh, rn, d_width, d_height
        
    def get_layout_params(self):
        fsize = max(10, min(24, 80 / math.pow(max(1, self.rn), 0.15)))
        w_mult = (max(3, self.max_cpw) * fsize) / 72.0 + 0.6
        h_mult = (self.max_lpl * fsize * 1.5) / 72.0 + 0.2
        width, height = self.d_width * w_mult, self.d_height * h_mult
        if self.d_width == 1 and self.d_height > 3 and height > width * 2.5:
            height = self.d_height * ((width * 2.5) / self.d_height)
        return {"figsize": (width, height), "fontsize": int(fsize), "textpad": (0.1, 0.15), "fontsize_types": max(12, int(fsize * 0.4))}

def get_recursive_stats(d, visited=None):
    if visited is None: visited = set()
    max_cpw, max_lpl, box_count = 1.0, 1.0, 0
    
    def walk(obj):
        nonlocal max_cpw, max_lpl, box_count
        if id(obj) in visited: return
        visited.add(id(obj))
        if isinstance(obj, monoidal.Bubble): return walk(obj.inside)
        if hasattr(obj, "boxes") and len(obj.boxes) == 1 and obj.boxes[0] is obj:
            label = str(getattr(obj, "drawing_name", getattr(obj, "name", ""))) or ""
            lines, wires = label.split('\n'), max(1, len(getattr(obj, "dom", [])), len(getattr(obj, "cod", [])))
            max_cpw, max_lpl, box_count = max(max_cpw, max(len(l) for l in lines) / wires), max(max_lpl, len(lines)), box_count + 1
            return
        if hasattr(obj, "__iter__"): [walk(b) for layer in obj if hasattr(layer, "boxes") for b in layer.boxes]
        elif hasattr(obj, "inside"): walk(obj.inside)
        elif hasattr(obj, "boxes"): [walk(b) for b in obj.boxes]
    walk(d)
    return max_cpw, max_lpl, box_count

STYLES = {
    "Scalar": {"color": "#ffffff", "spider": True, "fmt": lambda n, b: f"{getattr(b, 'tag', '')} {getattr(b, 'value', '')}".strip() or ""},
    "Alias": {"color": "#3498db", "spider": True, "fmt": lambda n, b: f"*{getattr(b, 'name', n.lstrip('*'))}"},
    "Anchor": {"color": "#2980b9", "spider": True, "fmt": lambda n, b: f"&{getattr(b, 'name', n.lstrip('&'))}"},
    "Label": {"color": "#ffffff"}, "Data": {"color": "#fff9c4"}, "Eval": {"color": "#ffccbc", "name": "exec"},
    "Curry": {"color": "#d1c4e9", "name": "Λ"}, "Program": {"color": "#ffffff"},
    "Copy": {"color": "#2ecc71", "spider": True, "name": "Δ"}, "Merge": {"color": "#27ae60", "spider": True, "name": "μ"},
    "Discard": {"color": "#e74c3c", "spider": True, "name": "ε", "check": lambda b: b.dom.name != ""},
    "Swap": {"color": "#f1c40f", "swap": True, "name": ""},
    "Sequence": {"color": "#ffffff", "bubble": True, "fmt": lambda n, b: f"[{getattr(b, 'tag', '')}]" if getattr(b, 'tag', '') else ""},
    "Mapping": {"color": "#ffffff", "bubble": True, "fmt": lambda n, b: f"{{{getattr(b, 'tag', '')}}}" if getattr(b, 'tag', '') else ""},
}

def get_style(box):
    cls, name = type(box).__name__, str(getattr(box, "drawing_name", getattr(box, "name", "")))
    key = next((k for k in STYLES if cls == k or name.startswith(k) or (k == "Eval" and name=="eval") or (k == "Curry" and name=="curry") or (k=="Data" and name.startswith("⌜"))), None)
    style = STYLES.get(key, {})
    final_name = style.get("name", name)
    if "fmt" in style: final_name = style["fmt"](name, box)
    if "check" in style and not style["check"](box): final_name, style = "", {"color": "#ffffff", "spider": True}
    return final_name, style.get("color", "#f0f0f0"), style.get("spider", False), style.get("swap", False), style.get("bubble", False)

def diagram_draw(path: Path, fd):
    m_cpw, m_lpl, rn = get_recursive_stats(fd)
    params = ComplexityProfile(m_cpw, m_lpl, rn, getattr(fd, "width", len(getattr(fd, "dom", [])) or 1), len(fd) if hasattr(fd, "__iter__") else 1).get_layout_params()
    out_svg, out_png = (str(path), None) if path.suffix.lower() in ['.png', '.jpg', '.jpeg'] else (str(path.with_suffix(".svg")), str(path.with_suffix(".png")))
    
    def map_ob(ob): return monoidal.Ty(*[getattr(o, "name", str(o)) for o in ob.inside])
    
    def map_ar(box):
        name, color, spider, swap, bubble = get_style(box)
        dom, cod = map_ob(box.dom), map_ob(box.cod)
        if spider: res = monoidal.Box(name, dom, cod, drawing_name=name)
        else:
            padded = "\n".join([l.ljust(int(m_cpw * max(1, len(dom), len(cod)))) for l in str(name).split('\n')])
            if bubble or (isinstance(box, monoidal.Bubble) and not spider):
                inside = standardize(box.inside) if hasattr(box, 'inside') else monoidal.Box(padded, dom, cod)
                res = monoidal.Bubble(inside, dom, cod, drawing_name=padded)
            else:
                res = monoidal.Box(padded, dom, cod, drawing_name=padded)
                if not swap: res.nodesize = (1, 1)
        res.color, res.draw_as_spider, res.draw_as_swap = color, spider, swap
        if spider: res.shape, res.nodesize = "circle", (1.5, 1.5)
        return res
    
    def standardize(diag):
        if not hasattr(diag, "boxes_and_offsets"): return diag
        m_dom, curr, inside = map_ob(diag.dom), map_ob(diag.dom), []
        for box, off in diag.boxes_and_offsets:
            mbox = map_ar(box)
            layer = monoidal.Layer(monoidal.Id(curr[:off]), mbox, monoidal.Id(curr[off + len(mbox.dom):]))
            inside.append(layer)
            curr = layer.cod
        return monoidal.Diagram(inside, m_dom, curr)
    
    fd_draw = standardize(fd)
    draw_params = {"aspect": "auto", "figsize": params["figsize"], "fontsize": params["fontsize"], "fontfamily": "monospace", "textpad": params["textpad"], "fontsize_types": params["fontsize_types"]}
    fd_draw.draw(path=out_svg, **draw_params)
    if out_png:
        try: fd_draw.draw(path=out_png, **draw_params)
        except: pass
