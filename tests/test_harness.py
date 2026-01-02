import pytest
import subprocess
import glob
import os
import sys

# Find all test cases
TEST_DIR = os.path.dirname(__file__)
TEST_CASES = sorted(glob.glob(os.path.join(TEST_DIR, "*.test.yaml")))

@pytest.mark.parametrize("test_file", TEST_CASES)
def test_case(test_file):
    # Determine the log file path
    log_file = test_file.replace(".test.yaml", ".log")

    # Check if log file exists
    assert os.path.exists(log_file), f"Log file missing for {test_file}"

    # Read input and expected output
    with open(test_file, "r") as f:
        input_content = f.read()

    with open(log_file, "r") as f:
        expected_output = f.read()

    # Run the shell
    # Use the 'titi' command which should be in the PATH after installation
    # Or use python -m titi
    cmd = [sys.executable, "-m", "titi", test_file]

    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        check=False
    )

    # Assert output
    assert result.stdout == expected_output
