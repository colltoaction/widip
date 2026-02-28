import pytest

from widip.loader import repl_read
from widip.widish import SHELL_RUNNER


@pytest.mark.parametrize(["yaml_text", "stdin", "expected"], [
    ["scalar",             "",   "scalar"],
    ["? scalar",           "",   "scalar"],
    ["- scalar",           "",   "scalar"],
    ["!printf scalar",     "",   "scalar"],
    ["!echo scalar",       "",   "scalar\n"],
])
def test_shell_runner(yaml_text, stdin, expected):
    # TODO deduplicate with widish_main
    fd = repl_read(yaml_text)
    constants = tuple(x.name for x in fd.dom)
    assert SHELL_RUNNER(fd)(*constants)(stdin) == expected
