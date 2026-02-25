import pytest

from widip.lang import Box, Ty
from widip.loader import repl_read

@pytest.mark.parametrize(["yaml_text", "expected_box"], [
    [
        "some spaced scalar",
        Box("⌜−⌝", Ty("some spaced scalar"), Ty() >> Ty("some spaced scalar"))],
    [
        "!tagged scalar",
        Box("tagged", Ty("scalar"), Ty("tagged") >> Ty("tagged"))],
])
def test_loader_enconding(yaml_text, expected_box):
    assert repl_read(yaml_text) == expected_box
