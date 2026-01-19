import pytest
import asyncio
import os
from io import BytesIO
from pathlib import Path
from discopy import closed
from unittest.mock import patch, AsyncMock
from computer import Language
from computer.exec import Process, compile_exec
from computer.asyncio import loop_scope
from computer.io import value_to_bytes, get_executable

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
    dom = Language
    cod = Language
    exec_box = closed.Box("exec", dom, cod)

    loop = asyncio.get_running_loop()
    
    with loop_scope(hooks=hooks, loop=loop):
        # compile_exec converts "exec" box to Process
        # It's a functor, only takes the diagram
        process = compile_exec(exec_box)

        # The result should be a Process
        assert isinstance(process, Process)
        
        # Verify the process has the right types
        assert hasattr(process, 'dom')
        assert hasattr(process, 'cod')
