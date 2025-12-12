from discopy.closed import Ty, Box, Id
from widip.widish import SHELL_RUNNER, IO

def test_io_constant():
    # Box("⌜−⌝", Ty(), Ty("io")) - empty domain
    box = Box("⌜−⌝", Ty(), Ty("io"))
    io = SHELL_RUNNER(box)
    assert isinstance(io, IO)
    res = io()
    assert res == ""

    # Box("⌜−⌝", Ty("hello"), Ty("io")) - domain with value
    # In widip, this acts as Identity (passing the value through)
    # The value "hello" in Ty("hello") is just a type name/annotation.
    box2 = Box("⌜−⌝", Ty("hello"), Ty("io"))
    io2 = SHELL_RUNNER(box2)

    # Must call with arguments matching domain
    res2 = io2("input_val")
    assert res2 == "input_val"

def test_io_sequence():
    # Test (;) logic
    r1 = IO(lambda *args: "R1", (str,), (str,))
    r2 = IO(lambda *args: "R2" + args[0] if args else "R2", (str,), (str,))

    seq_box = Box("(;)", Ty("io", "io"), Ty("io"))
    seq_runner = SHELL_RUNNER(seq_box)

    composed_runner = seq_runner(r1, r2)
    assert isinstance(composed_runner, IO)

    res = composed_runner("start")
    assert res == "R2R1"

def test_io_parallel():
    # Test (||) logic
    k1 = IO(lambda *args: "K1", (str,), (str,))
    v1 = IO(lambda *args: "V1" + args[0], (str,), (str,))

    par_box = Box("(||)", Ty("io", "io"), Ty("io"))
    par_runner = SHELL_RUNNER(par_box)

    mapped_runner = par_runner(k1, v1)

    res = mapped_runner("start")
    assert res == "V1K1"

def test_g_box():
    # Box("G", Ty(tag, v), Ty("io"))
    g_box = Box("G", Ty("echo", "hello"), Ty("io"))
    g_io = SHELL_RUNNER(g_box)

    # g_io takes (tag, v) and returns runner
    runner = g_io("echo", "hello")
    assert isinstance(runner, IO)

    # runner executes `echo hello` with input "input"
    res = runner("input")
    assert res == "hello"
