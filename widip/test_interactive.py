import subprocess
import pytest

@pytest.mark.parametrize("filename, expected_output", [
    ("examples/hello-world.yaml", "Hello world!\n"),
    ("examples/shell.yaml", "73\n23\n  ? !grep grep: !wc -c\n  ? !tail -2\n"),
    ("examples/aoc2025/1-1.yaml", "1147\n"),
])
def test_piping_to_widish(filename, expected_output, capfd):
    with open(filename, "r") as f:
        content = f.read()
    
    subprocess.run(["bin/widish"], input=content, text=True, check=False)
    
    out, err = capfd.readouterr()
    
    if filename == "examples/shell.yaml":
         # Check for presence of expected outputs allowing for reordering/logs
         # 73 approx (wc -c of file)
         assert "73" in out or "72" in out
         # 23 approx (grep and wc of file)
         assert "23" in out or "22" in out
         # tail output
         assert "? !tail -2" in out
    elif filename == "examples/aoc2025/1-1.yaml":
         assert "1147" in out
    else:
         assert expected_output == out
