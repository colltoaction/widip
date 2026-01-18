
import pytest
import subprocess
import os
from pathlib import Path

# --- Helpers ---

def run_titi(filename):
    """Executes a titi file and returns the output string."""
    path = Path(filename)
    if not path.exists():
        pytest.fail(f"{path} does not exist")
        
    result = subprocess.run(
        ["python", "-m", "titi", str(path)], 
        capture_output=True, 
        text=True
    )
    assert result.returncode == 0
    return result.stdout

def read_file(filename):
    """Reads file content."""
    with open(filename, "r") as f:
        return f.read()

def normalize_output(output, expected):
    """Normalizes output by stripping trailing newline if expected doesn't have one."""
    if output == expected + "\n":
        return output.strip(), expected.strip()
    return output, expected

# --- Tests ---

@pytest.mark.parametrize("filename", [
    "examples/quine.yaml",
    "examples/quine2.yaml",
])
def test_simple_quine(filename):
    """Test that file produces its own source code as output."""
    source_code = read_file(filename)
    output = run_titi(filename)
    
    output, source_code = normalize_output(output, source_code)
    
    assert output == source_code, f"Failed for {filename}"

@pytest.mark.parametrize("file_a, file_b", [
    ("examples/ping.yaml", "examples/pong.yaml"),
    ("examples/pong.yaml", "examples/ping.yaml"),
])
def test_relay_quine(file_a, file_b):
    """Test that file_a outputs the source of file_b."""
    source_b = read_file(file_b)
    output_a = run_titi(file_a)
    
    output_a, source_b = normalize_output(output_a, source_b)
    
    assert output_a == source_b, f"{file_a} did not output source of {file_b}"

def test_mutation_quine():
    """Test that the mutating quine produces a next generation of itself."""
    filename = "examples/mutation.yaml"
    
    # 1. Read Gen 1 (Original)
    gen1_src = read_file(filename)
    assert "# generation: 1" in gen1_src
    
    # 2. Run Gen 1 -> Gen 2
    output = run_titi(filename)
    if output.endswith("\n") and not gen1_src.endswith("\n"):
        output = output[:-1]
    gen2_src = output

    # Verify Gen 2
    assert "# generation: 2" in gen2_src
    assert "# generation: 1" not in gen2_src
    
    # 3. Validating the "Quine" property (Functional Equivalence)
    # temporarily overwrite the file with Gen 2 to see if it produces Gen 3
    
    original_path = Path(filename)
    
    try:
        # Write Gen 2 to file
        with open(original_path, "w") as f: 
            f.write(gen2_src)
        
        # Run Gen 2 (on disk) -> Gen 3
        output3 = run_titi(filename)
        gen3_src = output3
        if gen3_src.endswith("\n") and not gen2_src.endswith("\n"):
             gen3_src = gen3_src[:-1]

        assert "# generation: 3" in gen3_src
        assert "# generation: 2" not in gen3_src
        
    finally:
        # Restore
        with open(original_path, "w") as f: 
            f.write(gen1_src)
