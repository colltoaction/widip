from computer.yaml import impl_parse
import sys

src = "!echo hello\n!echo world"
try:
    diag = impl_parse(src)
    print(f"Parsed diagram: {diag}")
    from computer.yaml import load
    composed = load(src)
    print(f"Composed diagram: {composed}")
    print(f"Dom: {composed.dom}, Cod: {composed.cod}")
except Exception as e:
    print(f"Error: {e}")
