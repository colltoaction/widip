import pytest

from discopy import closed, monoidal

from widip.lang import Box, Ty, Id
from widip.loader import repl_read

@pytest.mark.parametrize(["yaml_text", "expected_box"], [
    [
        "some spaced scalar",
        Box("⌜−⌝", Ty("some spaced scalar"), Ty() >> Ty("some spaced scalar"))],
    [
        "!tagged scalar",
        Box("tagged", Ty("scalar"), Ty("tagged") >> Ty("tagged"))],
    [
        "!just_tag",
        Box("just_tag", Ty(""), Ty("just_tag") >> Ty("just_tag"))],
    [
        "",
        Id(Ty())],
])
def test_loader_encoding(yaml_text, expected_box):
    assert repl_read(yaml_text) == expected_box
