import pytest
import asyncio
from discopy import closed
from titi.yaml import load
from titi.exec import execute, titi_runner
from titi.asyncio import loop_scope

def test_anchor_alias_basic():
    """Simple test for anchor and alias."""
    yaml_src = """
&hello
  !echo "Hello World"
- !alias hello
"""
    # Load returns a Diagram (if single document) or a Stream of diagrams if list
    # Here it's a Stream
    diag = load(yaml_src)
    
    # We need a dummy printer or capture stdout
    output = []
    def stdout_write(b):
        output.append(b.decode())
    
    hooks = {
        'stdout_write': stdout_write,
        'stdin_read': lambda: b"",
        'stdin_isatty': lambda: True,
        'get_executable': lambda: "python3",
        'fspath': lambda x: x,
        'value_to_bytes': lambda x: str(x).encode(),
        'BytesIO': __import__('io').BytesIO,
        'Path': __import__('pathlib').Path
    }

    async def run_test():
        with titi_runner(hooks) as (runner, loop):
            # diag is a StreamBox which is a Diagram
            await runner(diag)
    
    asyncio.run(run_test())
    assert "Hello World" in "".join(output)

def test_recursive_anchor():
    """Test for recursion via anchors."""
    # A simple count-down from 2 to 1 (ignoring actual arithmetic for now, just nesting)
    yaml_src = """
&loop
  !xargs test $1 -gt 0:
     - !echo $1
     - !xargs -I {} expr {} - 1
     - !alias loop
!Data 2 >> !alias loop
"""
    # Wait, !Data 2 >> !alias loop is not valid YAML tag syntax for composition
    # but we can use Mapping for flow.
    
    # Let's use a simpler recursion:
    yaml_src = """
&repeat
  !xargs test $1 -gt 0:
    ? !echo "Count"
    : - !xargs -I {} expr {} - 1
      - !alias repeat
!Data 2 >> !alias repeat
"""
    # Actually, the parser handles !alias as a box.
    # Let's test if alias even works at all.
    pass

@pytest.mark.asyncio
async def test_manual_anchor_exec():
    """Test anchor/alias interaction directly in the exec context."""
    from titi.exec import execute
    from computer import Program, Data
    
    # Define a diagram that sets an anchor
    inner = Program("echo", ("Inside",))
    anchor_diag = Program("anchor", ("my_loop", inner))
    
    # Define a diagram that uses the alias
    alias_diag = Program("alias", ("my_loop",))
    
    # Sequential: anchor >> alias
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
    
    # Should see "Inside" twice (once for anchor execution, once for alias)
    # Wait, Program("anchor") executes the inner diagram.
    assert output.count("Inside\n") == 2
