
import pytest
from computer import Data, Program, Partial, Copy, Merge, Discard
from computer.core import Language
from titi.exec import titi_runner
from titi.asyncio import unwrap
from discopy import closed

# --- Fixtures ---

@pytest.fixture
def run_diag():
    """Helper to run a diagram and return the result."""
    hooks = {
        'value_to_bytes': lambda x: str(x).encode(),
        'stdin_read': lambda: b"",
        'stdout_write': lambda x: None,
        'fspath': lambda x: x,
        'get_executable': lambda: "python",
    }
    with titi_runner(hooks) as (runner, loop):
        async def _run(diag, stdin=None):
            res = await unwrap(runner(diag, stdin), loop)
            # Unpack single-element tuple result if applicable
            if isinstance(res, tuple) and len(res) == 1:
                return res[0]
            return res
        yield _run

# --- Parametrized Tests ---

@pytest.mark.asyncio
@pytest.mark.parametrize("diag_factory, expected", [
    (lambda: Data("hello"), "hello"),
    (lambda: Discard(Language) >> Data("hello", dom=closed.Ty()), "hello"),
])
async def test_data_logic(run_diag, diag_factory, expected):
    """Test Data box logic."""
    d = diag_factory()
    res = await run_diag(d, stdin="ignored" if isinstance(d.dom, closed.Ty) and len(d.dom)==0 else None)
    assert res == expected

@pytest.mark.asyncio
@pytest.mark.parametrize("n_copies", [2, 3])
async def test_copy_logic(run_diag, n_copies):
    """Test Copy logic for multiple outputs."""
    diag = Data("X") >> Copy(Language, n_copies)
    res = await run_diag(diag)
    assert res == tuple("X" for _ in range(n_copies))

@pytest.mark.asyncio
@pytest.mark.parametrize("inputs, expected", [
    (["A", "B"], "B"),  # Shadowing
    (["A", None], "A"), # None skipping (conceptual, inputs here are raw data)
])
async def test_merge_logic(run_diag, inputs, expected):
    """Test Merge logic priorities."""
    # Construct merge inputs: Data(inputs[0]) @ Data(inputs[1])...
    # Note: inputs are strings, None data isn't directly supported by Data() usually
    # But let's assume Data handles string.
    
    if inputs[1] is None:
         pytest.skip("Skipping None merge test - need reliable None source")
         
    diag = (Data(inputs[0]) @ Data(inputs[1])) >> Merge(Language, 2)
    res = await run_diag(diag)
    assert res == expected

@pytest.mark.asyncio
async def test_program_execution(run_diag):
    """Test simple program execution using echo with static args."""
    # Program("echo", ["hello"]) -> runs 'echo hello'
    # Data input is ignored by echo
    cmd_box = Program("echo", ["hello"])
    p = Data("ignore") >> cmd_box
    res = await run_diag(p)
    
    if res is None:
         pytest.fail("Program execution returned None (failed?)")

    if hasattr(res, 'read'):
        content = await res.read()
        assert content.strip() == b"hello"
    else:
        assert res.strip() == b"hello"

# --- Quine Logic Tests ---

@pytest.mark.asyncio
@pytest.mark.parametrize("source", [
    "Data('X')",
    "SimpleQuine",
])
async def test_constructive_replication(run_diag, source):
    """Test constructive replication (Data identity)."""
    d = Data(source)
    res = await run_diag(d)
    assert res == source

@pytest.mark.asyncio
async def test_ouroboros_cycle(run_diag):
    """Test 2-cycle Logic (A->B, B->A)."""
    diag_a = Data("B")
    diag_b = Data("A")
    assert await run_diag(diag_a) == "B"
    assert await run_diag(diag_b) == "A"
