from titi.yaml import impl_parse, compose_functor, construct_functor
from discopy import closed

src = "&hello !echo world\n---\n*hello"
print(f"--- SOURCE ---\n{src}\n")

# 1. Parse to representation boxes
rep = compose_functor(impl_parse(src))
print(f"Representation Diagram: {rep}")

def print_nested(diag, indent=""):
    for i, box in enumerate(diag.boxes):
        print(f"{indent}Box {i}: {box.name} (kind: {getattr(box, 'kind', 'N/A')}, tag: {getattr(box, 'tag', 'N/A')})")
        nested = getattr(box, 'nested', None)
        if nested is not None:
            if hasattr(nested, 'boxes'):
                print_nested(nested, indent + "  ")
            else:
                print(f"{indent}  Nested (not diagram): {type(nested)}")

print_nested(rep)

# 2. Compile to Language boxes
diag = construct_functor(rep)
print(f"\nCompiled Diagram: {diag}")
for i, box in enumerate(diag.boxes):
    print(f"Compiled Box {i}: {box.name} (args: {getattr(box, 'args', 'N/A')})")
