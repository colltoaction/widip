
import pytest
import subprocess
from pathlib import Path

def test_quine():
    """Test that examples/quine.yaml produces its own source code as output."""
    quine_path = Path("examples/quine.yaml")
    
    # Ensure the quine file exists (will be created by the agent)
    if not quine_path.exists():
        pytest.fail(f"{quine_path} does not exist")
        
    with open(quine_path, "r") as f:
        source_code = f.read()
        
    # Run titi on the quine file
    # We pipe the source as stdin just in case, but titi should read the file from args
    result = subprocess.run(
        ["python", "-m", "titi", str(quine_path)], 
        capture_output=True, 
        text=True
    )
    
    output = result.stdout
    
    # Debug info
    print(f"Source len: {len(source_code)}")
    print(f"Output len: {len(output)}")
    print(f"Source: {source_code!r}")
    print(f"Output: {output!r}")

    assert result.returncode == 0
    assert output == source_code
