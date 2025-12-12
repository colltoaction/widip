import pytest
from widip.representing import discopy_to_hif
from discopy.closed import Box, Ty
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
