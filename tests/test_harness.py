import pytest
import subprocess
import glob
import os

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
    # Assuming running from repo root
    cmd = ["bin/widish", test_file]

    try:
        proc = subprocess.run(
            ["python", "-m", "widip", test_file],
            capture_output=True,
            text=True,
            timeout=2.0
        )
    except subprocess.TimeoutExpired as e:
        proc = e # Store the exception object to access stdout/stderr if needed, or handle differently
        # For this specific case, we might want to assert on the timeout itself or its output
        # For now, we'll let the assert below fail if proc doesn't have .stdout
        # Or, more robustly, handle the timeout as a specific test outcome.
        # Given the original code structure, we'll assume `proc` should behave like `result`.
        # If a timeout occurs, e.stdout and e.stderr contain the output captured before timeout.
        pass # The assert below will then use proc.stdout (which is e.stdout)

    # Assert output
    assert proc.stdout == expected_output
