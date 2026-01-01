import pytest
from discopy import closed
from unittest.mock import patch, AsyncMock
from .compiler import Exec
from .widish import SHELL_RUNNER, Process

@pytest.mark.asyncio
async def test_exec_runner():
    # Test execution logic.
    # We want to verify that running the process calls run_command with appropriate args.

    # Exec(dom, cod)
    # dom = "input"
    # cod = "output"
    # dom = "input" -> Ty("IO") for piping semantics
    # cod = "output" -> Ty("IO")
    dom = closed.Ty("IO")
    cod = closed.Ty("IO")
    exec_box = Exec(dom, cod)

    # SHELL_RUNNER converts Exec to Process
    process = SHELL_RUNNER(exec_box)

    # The process should:
    # 1. Start with inputs corresponding to dom.
    # 2. Add Constant (Gamma) -> "bin/widish"
    # 3. Call Eval("bin/widish", inputs)
    # Eval should trigger _deferred_exec_subprocess (or similar logic for Eval).

    # We need to mock run_command in widish.py
    with patch("widip.widish.run_command", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = "executed"

        # Run the process.
        result = process("some_input")

        # If result is awaitable, await it.
        from widip.thunk import unwrap
        final_result = await unwrap(result)

        assert final_result == "executed"

        # Verify call arguments
        # args passed to run_command: name, cmd_args, stdin
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        # name, args, stdin
        assert call_args[0][0] == "bin/widish"
        assert call_args[0][1] == ()
        assert call_args[0][2] == "some_input"
