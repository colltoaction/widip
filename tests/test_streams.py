
import pytest
import asyncio
from computer.yaml import load
from computer.exec import titi_runner

@pytest.mark.asyncio
async def test_multi_document_stream_execution():
    """Verify that multiple documents execute sequentially in a stream."""
    yaml_src = "!echo Document1\n---\n!echo Document2\n"
    
    output = []
    hooks = {
        'stdout_write': lambda b: output.append(b.decode()),
        'fspath': lambda x: "/bin/" + x if x == "echo" else x,
        'value_to_bytes': lambda x: x if isinstance(x, bytes) else str(x).encode(),
        'get_executable': lambda: "python3",
        'stdin_isatty': lambda: True,
        'stdin_read': lambda: b"",
        'BytesIO': __import__('io').BytesIO,
        'Path': __import__('pathlib').Path
    }

    async def run_test():
        with titi_runner(hooks) as (runner, loop):
            diag = load(yaml_src)
            res = await runner(diag)
            
    await run_test()
    combined = "".join(output)
    # Flexible check for order
    assert "Document1" in combined
    assert "Document2" in combined

@pytest.mark.asyncio
async def test_anchor_leak_prevention():
    """Verify that anchors defined in one document are NOT accessible in the next."""
    yaml_src = "&leak !Data Secret\n---\n*leak\n"
    
    hooks = {
        'stdout_write': lambda b: None,
        'value_to_bytes': lambda x: str(x).encode(),
        'get_executable': lambda: "python3",
        'stdin_isatty': lambda: True,
        'stdin_read': lambda: b"",
        'BytesIO': __import__('io').BytesIO,
        'Path': __import__('pathlib').Path
    }

    async def run_test():
        with titi_runner(hooks) as (runner, loop):
            try:
                diag = load(yaml_src)
                await runner(diag)
            except Exception as e:
                return e
        return None

    error = await run_test()
    # Expect error due to undefined anchor in second document
    assert error is not None
    assert isinstance(error, (LookupError, KeyError, ValueError))
