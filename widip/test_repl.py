import pytest
import asyncio
from unittest.mock import MagicMock
from pathlib import Path
from io import BytesIO

from discopy import closed
from widip.repl import read, env, get_source, eval_print, repl_read, file_diagram
from widip.computer import interpreter, compiler
from widip.exec import widip_runner

@pytest.fixture
def loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

# --- Adaptations of test_read from shell.py ---

@pytest.mark.asyncio
async def test_read_file_handling(loop):
    """
    Test that repl.py can read and parse a file.
    Adapted from test_shell.py::test_read
    """
    # Create a dummy yaml file
    import tempfile
    import os

    content = """
    x:
        tag: !eval
        inside: "2+2"
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(content)
        f_path = f.name

    try:
        # Simulate what get_source does when reading a file
        fd = file_diagram(f_path)

        # Verify that we got a diagram
        assert fd is not None
        # Basic check to ensure it's a diagram (or whatever file_diagram returns)
        # It should return a Diagram
        assert hasattr(fd, 'boxes') or hasattr(fd, 'inside')

        # We can also check if `read` yields the expected values
        # read(fd, path, file_name, loop)
        gen = read(fd, Path(f_path), f_path, loop)

        item = await anext(gen)
        # Item is (diagram, path, input_stream)
        assert item[0] is not None
        assert item[1] == Path(f_path)

    finally:
        os.remove(f_path)


# --- Adaptations of test_eval from shell.py and rep.py ---

@pytest.mark.asyncio
async def test_eval_logic(loop):
    """
    Test execution of an eval-like construct.
    Adapted from test_shell.py::test_eval and test_rep.py::test_eval
    """
    from widip.computer import Program, Language

    # Test case: Eval "2+2" using python3 -c
    program = Program("python3", Language, Language, ("-c", "print(2+2)"))

    output_captured = []

    async def capture_output(rec, val):
        output_captured.append(val)

    with widip_runner(executable="python3", loop=loop) as (runner, _):
        pipeline = lambda fd: runner(compiler(fd, compiler, None))

        # We need a source iterator
        async def source_gen():
            yield program, Path("test"), BytesIO(b"")

        await interpreter(pipeline, source_gen(), loop, capture_output)

    assert len(output_captured) > 0
    # The output is likely a SubprocessStream object or tuple containing it
    # We need to read from it to verify content

    result = output_captured[0]
    if isinstance(result, tuple):
        result = result[0]

    if hasattr(result, 'read'):
        content = await result.read()
        assert content.strip() == b"4"
    else:
        # Fallback if it was already read
        assert str(result).strip() == "4"


# --- Adaptations of test_print from shell.py ---

@pytest.mark.asyncio
async def test_print_logic(loop):
    """
    Test output handling.
    Adapted from test_shell.py::test_print
    """
    # We want to verify that output is correctly passed to the output handler.

    from widip.computer import Data, Language

    # A Data box simply holds a value.
    data_box = Data("Hello World", Language, Language)

    output_captured = []

    async def capture_output(rec, val):
        output_captured.append(val)

    with widip_runner(loop=loop) as (runner, _):
        pipeline = lambda fd: runner(compiler(fd, compiler, None))

        async def source_gen():
            yield data_box, Path("test"), BytesIO(b"")

        await interpreter(pipeline, source_gen(), loop, capture_output)

    assert len(output_captured) > 0
    # Data box returns tuple
    assert "Hello World" in str(output_captured[0])


# --- Adaptations of parameter tests from rep.py ---

@pytest.mark.asyncio
async def test_params_logic(loop):
    """
    Test passing arguments.
    Adapted from test_rep.py parameter tests.
    """
    # Test passing arguments to a Program.
    from widip.computer import Program, Language, Copy

    # Let's test a simple Copy box.
    copy_box = Copy(Language, 2)

    output_captured = []
    async def capture_output(rec, val):
        output_captured.append(val)

    # Input stream content
    input_content = b"test_input"
    input_stream = BytesIO(input_content)

    with widip_runner(loop=loop) as (runner, _):
        pipeline = lambda fd: runner(compiler(fd, compiler, None))

        async def source_gen():
            # yield diagram, path, input_stream
            yield copy_box, Path("test"), input_stream

        await interpreter(pipeline, source_gen(), loop, capture_output)

    assert len(output_captured) == 1
    res_tuple = output_captured[0]
    assert isinstance(res_tuple, tuple)
    assert len(res_tuple) == 2

    # Verify content
    val1 = res_tuple[0]
    val2 = res_tuple[1]

    assert val1 is val2
    if hasattr(val1, 'getvalue'):
        assert val1.getvalue() == input_content
