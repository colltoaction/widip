from titi.yaml import load
from discopy import closed

src = "&hello !echo world\n*hello"
diag = load(src)
print(f"Diagram: {diag}")
for i, box in enumerate(diag.boxes):
    print(f"Box {i}: {box.name} (args: {getattr(box, 'args', 'N/A')})")
