import pytest
from discopy.closed import Curry, Eval

from widip.computer import Ty, Id
from widip.loader import repl_read


@pytest.mark.parametrize(["path", "yaml_text", "expected"], [
    [
        "empty_content.svg",
        "",
        Id(),
    ],
    [
        "scalar_only.svg",
        "a",
        Curry(Eval(Ty() >> Ty("a")), n=0, left=False),
    ],
    [
        "tagged_scalar.svg",
        "!X a",
        Curry(Eval(Ty("X") @ Ty("a") >> Ty()), n=2, left=False),
    ],
    [
        # implicit empty string
        "tag_only.svg",
        "!X",
        Curry(Eval(Ty("X") @ Ty("") >> Ty()), n=2, left=False),
    ],
    [
        "empty_string.svg",
        "''",
        Curry(Id(Ty() >> Ty()), n=1, left=True),
    ],
])
def test_loader_encoding(path, yaml_text, expected):
    actual = repl_read(yaml_text)
    assert actual == expected
