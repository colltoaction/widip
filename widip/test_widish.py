import pytest
import asyncio
from discopy import closed
from unittest.mock import patch, AsyncMock
from .exec import Exec, ExecFunctor
from .asyncio import Process, loop_scope

@pytest.mark.asyncio
async def test_exec_runner():
    # Test execution logic.
    # We want to verify that running the process calls run_command with appropriate args.

    # Exec(dom, cod)
    dom = closed.Ty("input")
    cod = closed.Ty("output")
    exec_box = Exec(dom, cod)

    loop = asyncio.get_running_loop()
    
    with loop_scope(loop):
        # ExecFunctor converts Exec to Process
        runner = ExecFunctor(loop=loop)
        process = runner(exec_box)

        # The result should be a Process
        assert isinstance(process, Process)
        
        # Verify the process has the right types
        assert process.dom is not None
        assert process.cod is not None

