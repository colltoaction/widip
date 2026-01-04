import pytest
import asyncio
from titi.yaml import load
from titi.exec import execute, titi_runner
from computer import Program, Data

@pytest.mark.parametrize("yaml_src, expected_output", [
    ("&hello !echo world\n*hello", ["world\n", "world\n"]),
    ("&fixed !Data data\n*fixed", ["data\n"]), # Data doesn't print by itself in execute, only returned. 
                                              # But if piped to printer...
])
def test_anchor_alias_execution(yaml_src, expected_output):
    """Test anchor/alias interaction in YAML execution."""
    output = []
    hooks = {
        'stdout_write': lambda b: output.append(b.decode()),
        'stdin_read': lambda: b"",
        'stdin_isatty': lambda: True,
        'get_executable': lambda: "python3",
        'fspath': lambda x: "/bin/" + x if x == "echo" else x,
        'value_to_bytes': lambda x: str(x).encode(),
        'BytesIO': __import__('io').BytesIO,
        'Path': __import__('pathlib').Path
    }

    async def run_test():
        with titi_runner(hooks) as (runner, loop):
            diag = load(yaml_src)
            await runner(diag)
    
    asyncio.run(run_test())
    # Note: anchor execution + alias execution = 2 prints for echo
    combined_output = "".join(output)
    if not any(expected in combined_output for expected in expected_output):
        print(f"DEBUG: captured output: {combined_output!r}")
    for expected in expected_output:
        assert expected in combined_output

@pytest.mark.asyncio
async def test_manual_anchor_exec():
    """Test anchor/alias interaction directly with Programs."""
    # Define a diagram that sets an anchor
    inner = Program("echo", ("Inside",))
    anchor_diag = Program("anchor", ("my_loop", inner))
    
    # Define a diagram that uses the alias
    alias_diag = Program("alias", ("my_loop",))
    
    # Sequence: anchor >> alias
    full_diag = anchor_diag >> alias_diag
    
    output = []
    hooks = {
        'stdout_write': lambda b: output.append(b.decode()),
        'fspath': lambda x: "/bin/" + x if x == "echo" else x,
        'value_to_bytes': lambda x: str(x).encode()
    }
    
    import asyncio
    loop = asyncio.get_running_loop()
    
    await execute(full_diag, hooks, "python3", loop, b"input")
    
    # Anchor execution prints "Inside", then Alias execution prints "Inside"
    assert output.count("Inside\n") == 2

@pytest.mark.parametrize("anchor_name", ["loop", "step", "rec"])
@pytest.mark.asyncio
async def test_parametrized_anchors(anchor_name):
    """Verify different anchor names work correctly."""
    inner = Program("echo", (anchor_name,))
    diag = Program("anchor", (anchor_name, inner)) >> Program("alias", (anchor_name,))
    
    output = []
    hooks = {
        'stdout_write': lambda b: output.append(b.decode()),
        'fspath': lambda x: "/bin/" + x if x == "echo" else x,
        'value_to_bytes': lambda x: str(x).encode()
    }
    
    loop = asyncio.get_running_loop()
    await execute(diag, hooks, "python3", loop)
    assert output.count(f"{anchor_name}\n") == 2
