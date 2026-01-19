from discopy import closed
P = closed.Ty("P")
box = closed.Box("data", closed.Ty(), P)
id_p = closed.Id(P)
layer = id_p @ box @ id_p
print(f"Layer dom: {layer.dom}")
print(f"Layer dom repr: {repr(layer.dom)}")
print(f"Layer dom objects: {layer.dom.inside}")

id_pp = closed.Id(P @ P)
try:
    res = id_pp >> layer
    print("Composition successful")
except Exception as e:
    print(f"Composition failed: {e}")
