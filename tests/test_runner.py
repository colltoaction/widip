import pytest

from discopy.utils import tuplify, untuplify

from widip.loader import repl_read
from widip.widish import SHELL_RUNNER


# TODO constants have to be tested, not test code
def run_diagram(fd, stdin):
    constants = tuple(x.name for x in fd.dom)
    result = SHELL_RUNNER(fd)(*constants)(stdin)
    return result


@pytest.mark.parametrize(["yaml_text", "stdin", "expected"], [
    ["scalar",             "",   "scalar"],
    ["? scalar",           "",   ("scalar", )],
    ["- scalar",           "",   "scalar"],
    ["!printf scalar",     "",   "scalar"],
    ["!echo scalar",       "",   "scalar\n"],
    ["{a, b, c}",          "",   ("a", "b", "c")],
    ["{a, !echo b, c}",    "",   ("a", "b\n", "c")],
    ["!printf { '%s %s %s', a, !echo b, c }", "", "a b\n c"],
    ["!echo {a, b, c}",    "",   "a b c\n"],
    ["!printf { '%s %s %s', a, b, c }", "", "a b c"],
    # Test document-level tag
    ["--- !echo doc content", "", "doc content\n"],
    [open("examples/hello-world.yaml"), "", "Hello world!\n"],
    [open("examples/shell.yaml"),       "", (('73\n', '23\n', '  ? !grep grep: !wc -c\n  ? !tail -2\n'), )],
    # Test with non-empty stdin
    ["!cat",               "foo", "foo"],
    ["!wc -c",             "foo", "3\n"],
    ["!grep foo",          "foo\nbar", "foo\n"],
])
def test_shell_runner(yaml_text, stdin, expected):
    result = run_diagram(repl_read(yaml_text), stdin)
    assert result == expected
