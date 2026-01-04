import pytest
from titi.yaml import load
from computer import Program, Data

@pytest.mark.parametrize("yaml_src, expected_name, expected_args", [
    ("&my_cmd !echo hello", "anchor", ("my_cmd",)),
    ("*my_cmd", "alias", ("my_cmd",)),
    ("!echo hello", "echo", ("hello",)),
])
def test_basic_compilation(yaml_src, expected_name, expected_args):
    """Verify basic YAML constructs compile to correct Program boxes."""
    diag = load(yaml_src)
    # Most basic tag/anchor constructs result in a single box in the diagram
    assert hasattr(diag, 'boxes')
    box = diag.boxes[0]
    assert box.name == expected_name
    
    # Check arguments
    if expected_name == "anchor":
        assert box.args[0] == expected_args[0]
        # For anchor, second arg is the inner diagram
        inner = box.args[1]
        assert hasattr(inner, 'boxes')
    else:
        assert box.args == expected_args

@pytest.mark.parametrize("yaml_src, expected_box_names", [
    ("- &step !echo Thinking\n- *step", ["anchor", "alias"]),
    ("!echo A >> !echo B", ["echo", "echo"]),
])
def test_composition_compilation(yaml_src, expected_box_names):
    """Verify composition of commands compiles correctly."""
    diag = load(yaml_src)
    assert [b.name for b in diag.boxes if b.name not in ["Δ", "μ", "ε"]] == expected_box_names

def test_mapping_compilation_wiring():
    """Verify Mapping compiles with fan-out (copy) and fan-in (merge)."""
    yaml_src = "key: value"
    diag = load(yaml_src)
    
    # Mapping structure: Δ >> (key @ value) >> μ
    # Plus potential Data("") if no outputs.
    names = [b.name for b in diag.boxes]
    assert "Δ" in names
    assert "μ" in names

@pytest.mark.parametrize("tag, value, expected_cmd", [
    ("xargs", "test 1 -eq 1", "xargs"),
    ("echo", "hello", "echo"),
])
def test_tag_compilation(tag, value, expected_cmd):
    """Verify specific tags compile to Program boxes."""
    yaml_src = f"!{tag} {value}"
    diag = load(yaml_src)
    box = diag.boxes[0]
    assert box.name == expected_cmd
    assert box.args == (value,)
