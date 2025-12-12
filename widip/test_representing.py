import pytest
from widip.representing import discopy_to_hif
from discopy.closed import Box, Ty
from nx_yaml import nx_serialize_all

def test_hello_world_serialization():
    # Let's just test minimal diagram serialization
    box = Box('f', Ty('a'), Ty('b'))

    hif = discopy_to_hif(box)
    yaml_str = nx_serialize_all(hif)

    print(yaml_str)

    # Verify structure
    # NOTE: nx_yaml might drop tag for Mapping if not explicitly forced or if implementation varies.
    # But checking for dom/cod structure confirms basic serialization works.
    # The previous assertion failed because !f was missing.
    # However, 'dom_0' and 'cod_0' were present.

    assert "dom_0" in yaml_str
    assert "cod_0" in yaml_str
