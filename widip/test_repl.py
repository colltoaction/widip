import pytest
import asyncio
from unittest.mock import MagicMock
from pathlib import Path
from io import BytesIO
import os

from discopy import closed
from widip.repl import read, env_fn, get_source, read_diagram
from widip.asyncio import eval_diagram
from widip.super import interpreter
from widip.compiler import SHELL_COMPILER as compiler
from widip.exec import widip_runner
from widip.io import value_to_bytes, get_executable

@pytest.fixture
def hooks():
    return {
        'set_recursion_limit': lambda n: None,
        'value_to_bytes': value_to_bytes,
        'stdout_write': lambda d: None,
        'stdin_read': lambda: "",
        'stdin_isatty': lambda: False,
        'get_executable': get_executable,
        'fspath': os.fspath,
        'BytesIO': BytesIO,
        'Path': Path
    }

@pytest.fixture
def loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest.mark.asyncio
async def test_read_file_handling(loop, hooks):
    """Test that repl.py can read and parse a file."""
    import tempfile
    content = """
    x:
        tag: !eval
        inside: "2+2"
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(content)
        f_path = f.name

    try:
        fd = read_diagram(f_path)
        assert fd is not None
        assert hasattr(fd, 'boxes') or hasattr(fd, 'inside')

        gen = read(fd, Path(f_path), f_path, loop, hooks)
        item = await anext(gen)
        assert item[0] is not None
        assert item[1] == Path(f_path)
    finally:
        os.remove(f_path)

@pytest.mark.asyncio
async def test_eval_logic(loop, hooks):
    """Test execution of an eval-like construct."""
    from widip.computer import Program, Language

    program = Program("python3", Language, Language, ("-c", "print(2+2)"))
    output_captured = []

    async def capture_output(rec, val):
        output_captured.append(val)

    with widip_runner(hooks=hooks, executable="python3", loop=loop) as (runner, _):
        pipeline = lambda fd: runner(compiler(fd, compiler, None))
        async def source_gen():
            yield program, Path("test"), BytesIO(b"")
        await interpreter(pipeline, source_gen(), loop, capture_output)

    assert len(output_captured) > 0
    result = output_captured[0]
    if isinstance(result, tuple):
        result = result[0]

    if hasattr(result, 'read'):
        content = await result.read()
        assert content.strip() == b"4"
    else:
        assert str(result).strip() == "4"

@pytest.mark.asyncio
async def test_print_logic(loop, hooks):
    """Test output handling."""
    from widip.computer import Data, Language
    data_box = Data("Hello World", Language, Language)
    output_captured = []

    async def capture_output(rec, val):
        output_captured.append(val)

    with widip_runner(hooks=hooks, loop=loop) as (runner, _):
        pipeline = lambda fd: runner(compiler(fd, compiler, None))
        async def source_gen():
            yield data_box, Path("test"), BytesIO(b"")
        await interpreter(pipeline, source_gen(), loop, capture_output)

    assert len(output_captured) > 0
    assert "Hello World" in str(output_captured[0])

@pytest.mark.asyncio
async def test_params_logic(loop, hooks):
    """Test passing arguments."""
    from widip.computer import Program, Language, Copy
    copy_box = Copy(Language, 2)
    output_captured = []
    async def capture_output(rec, val):
        output_captured.append(val)

    input_content = b"test_input"
    input_stream = BytesIO(input_content)

    with widip_runner(hooks=hooks, loop=loop) as (runner, _):
        pipeline = lambda fd: runner(compiler(fd, compiler, None))
        async def source_gen():
            yield copy_box, Path("test"), input_stream
        await interpreter(pipeline, source_gen(), loop, capture_output)

    assert len(output_captured) == 1
    res_tuple = output_captured[0]
    assert isinstance(res_tuple, tuple)
    assert len(res_tuple) == 2
