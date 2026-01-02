import subprocess
import pytest

@pytest.mark.parametrize("filename, expected_output", [
    ("examples/hello-world.yaml", "Hello world!\n"),
    ("examples/shell.yaml", "72\n22\n  ? !grep grep: !wc -c\n  ? !tail -2\n"),
    ("examples/aoc2025/1-1.yaml", "1147\n"),
    ("examples/countdown.yaml", "3\n2\n1\nLiftoff!\n"),
])
def test_piping_to_widish(filename, expected_output, capfd):
    with open(filename, "r") as f:
        content = f.read()
    
    subprocess.run(["python", "-m", "widip", filename], input=content, text=True, check=False)
    
    out, err = capfd.readouterr()
    if err:
        print(f"DEBUG_STDERR: {err}")
    assert expected_output == out
