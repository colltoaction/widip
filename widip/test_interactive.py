import subprocess
import pytest

@pytest.mark.parametrize("filename, expected_output", [
    ("examples/hello-world.yaml", "Hello world!\n"),
    ("examples/shell.yaml", "72\n22\n  ? !grep grep: !wc -c\n  ? !tail -2\n"),
    ("examples/aoc2025/1-1.yaml", "1147\n"),
])
def test_piping_to_widish(filename, expected_output, capfd):
    with open(filename, "r") as f:
        content = f.read()
    
    subprocess.run(["bin/widish"], input=content, text=True, check=False)
    
    out, err = capfd.readouterr()
    assert expected_output == out
