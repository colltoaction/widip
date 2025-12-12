import pytest
from widip.representing import discopy_to_hif
from discopy.closed import Box, Ty, Diagram, Id
from nx_yaml import nx_serialize_all

def test_custom_kind_mapping():
    # Test that box name is used as kind
    box = Box('mapping', Ty('a'), Ty('b'))

    hif = discopy_to_hif(box)
    yaml_str = nx_serialize_all(hif)

    print(yaml_str)

    # Check that we have a mapping with dom/cod keys
    assert "dom_0" in yaml_str
    assert "cod_0" in yaml_str

def test_scalar_kind():
    # Test scalar kind
    box = Box('scalar', Ty(), Ty(), data={'value': 'foo'})

    hif = discopy_to_hif(box)
    yaml_str = nx_serialize_all(hif)
    print(yaml_str)

    assert "foo" in yaml_str

def test_invalid_kind():
    # Test invalid kind (should fail in nx_yaml)
    box = Box('invalid_kind', Ty(), Ty())
    hif = discopy_to_hif(box)

    with pytest.raises(Exception):
        nx_serialize_all(hif)

def test_sequence_kind():
    # Test that 'sequence' kind produces an empty sequence (since it has no children logic implemented)
    box = Box('sequence', Ty(), Ty())
    hif = discopy_to_hif(box)
    yaml_str = nx_serialize_all(hif)
    print(yaml_str)

    # Empty sequence in YAML is []
    assert "[]" in yaml_str

def test_multiple_items():
    # Diagram with multiple boxes
    b1 = Box('scalar', Ty(), Ty(), data={'value': 'one'})
    b2 = Box('scalar', Ty(), Ty(), data={'value': 'two'})
    diagram = b1 >> b2

    hif = discopy_to_hif(diagram)
    yaml_str = nx_serialize_all(hif)
    print(yaml_str)

    assert "one" in yaml_str
    assert "two" in yaml_str
    # Should be a list
    assert yaml_str.strip().startswith("-")

def test_parallel_items():
    # Parallel boxes (tensor)
    b1 = Box('scalar', Ty(), Ty(), data={'value': 'left'})
    b2 = Box('scalar', Ty(), Ty(), data={'value': 'right'})
    diagram = b1 @ b2

    hif = discopy_to_hif(diagram)
    yaml_str = nx_serialize_all(hif)
    print(yaml_str)

    assert "left" in yaml_str
    assert "right" in yaml_str

def test_attributes():
    # Test extra attributes are passed to hif node
    # nx_yaml typically serializes attributes as tags or similar if configured,
    # or specific attributes like 'anchor', 'tag', 'value'.
    # Arbitrary attributes might be ignored by nx_yaml default serializer unless they match model.
    # But let's check if 'anchor' works.

    box = Box('scalar', Ty(), Ty(), data={'value': 'val', 'anchor': 'my_anchor'})
    hif = discopy_to_hif(box)
    yaml_str = nx_serialize_all(hif)
    print(yaml_str)

    assert "&my_anchor" in yaml_str
