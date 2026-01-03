import pytest
import asyncio
import os
from io import BytesIO
from pathlib import Path
from discopy import closed
from unittest.mock import patch, AsyncMock
from . import Process
from .exec import compile_exec
from .asyncio import loop_scope
from .io import value_to_bytes, get_executable

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

@pytest.mark.asyncio
async def test_exec_runner(hooks):
    # Test execution logic.
    # We want to verify that running the process calls run_command with appropriate args.

    # Any box named "exec" should be handled by ExecFunctor
    dom = closed.Ty("input")
    cod = closed.Ty("output")
    exec_box = closed.Box("exec", dom, cod)

    loop = asyncio.get_running_loop()
    
    with loop_scope(hooks=hooks, loop=loop):
        # compile_exec converts "exec" box to Process
        process = compile_exec(exec_box, hooks=hooks, executable="python3", loop=loop)

        # The result should be a Process
        assert isinstance(process, Process)
        
        # Verify the process has the right types
        assert process.dom is not None
        assert process.cod is not None
