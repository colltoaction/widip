import pytest
from discopy.closed import Curry

from widip.lang import Ty, Id
from widip.loader import repl_read


@pytest.mark.parametrize(["yaml_text", "expected"], [
    [
        "some spaced scalar",
        Curry(Id(Ty("some spaced scalar") >> Ty()), n=1, left=True),
    ],
    [
        "!tagged scalar",
        Curry(Id(Ty("tagged") @ Ty("scalar") >> Ty()), n=1, left=True),
    ],
    [
        "!just_tag",
        Curry(Id(Ty("just_tag") >> Ty()), n=1, left=False),
    ],
    [
        "''",
        Curry(Id(Ty() >> Ty()), n=1, left=True),
    ],
    [
        "",
        Id(Ty()),
    ],
])
def test_loader_encoding(yaml_text, expected):
    assert repl_read(yaml_text) == expected
