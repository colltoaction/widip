
import discopy
from discopy import frobenius, cat
from lib.computer.yaml import representation as ren

print(f"ren.Node type: {type(ren.Node)}")
print(f"ren.Node[0] type: {type(ren.Node[0])}")
print(f"frobenius.Ob: {frobenius.Ob}")
print(f"cat.Ob: {cat.Ob}")
print(f"Is instance? {isinstance(ren.Node[0], frobenius.Ob)}")

try:
    f = frobenius.Functor(ob={frobenius.Ty("Node"): ren.Node}, ar=lambda x: x)
    print("Functor creation successful")
    d = frobenius.Id(ren.Node)
    print("Diagram created")
    res = f(d)
    print("Functor application successful")
except Exception as e:
    print(f"Error: {e}")
