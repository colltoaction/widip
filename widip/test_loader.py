from discopy.closed import Box, Ty, Diagram, Id

from .loader import repl_read as compose_all


id_box = lambda i: Box("!", Ty(i), Ty(i))

def has_type(diagram, name):
    # Check if any type in the diagram involves 'name'
    for box in diagram.boxes:
        if any(name in str(obj) for obj in box.dom):
            return True
        if any(name in str(obj) for obj in box.cod):
            return True
    # Also check open wires (dom/cod of diagram itself)
    if any(name in str(obj) for obj in diagram.dom):
        return True
    if any(name in str(obj) for obj in diagram.cod):
        return True
    return False

def test_tagged():
    a0 = compose_all("!a")
    assert isinstance(a0, Diagram)
    assert has_type(a0, "a")

    a1 = compose_all("!a :")
    assert isinstance(a1, Diagram)
    assert has_type(a1, "a")

    a2 = compose_all("--- !a")
    assert isinstance(a2, Diagram)
    assert has_type(a2, "a")

    a3 = compose_all("--- !a\n--- !b")
    assert isinstance(a3, Diagram)
    assert has_type(a3, "a")
    assert has_type(a3, "b")

    a4 = compose_all("\"\": !a")
    assert isinstance(a4, Diagram)
    assert has_type(a4, "a")

    a5 = compose_all("? !a")
    assert isinstance(a5, Diagram)
    assert has_type(a5, "a")

def test_untagged():
    a0 = compose_all("")
    assert isinstance(a0, Diagram)

    a1 = compose_all("\"\":")
    assert isinstance(a1, Diagram)

    a2 = compose_all("\"\": a")
    assert isinstance(a2, Diagram)

    a3 = compose_all("a:")
    assert isinstance(a3, Diagram)

    a4 = compose_all("? a")
    assert isinstance(a4, Diagram)

def test_bool():
    # Correct path is src/data/category/bool.yaml
    path = "src/data/category/bool.yaml"
    import os
    if os.path.exists(path):
        with open(path) as f:
            t = compose_all(f)
            assert isinstance(t, Diagram)
            assert has_type(t, "true")
            assert has_type(t, "false")
