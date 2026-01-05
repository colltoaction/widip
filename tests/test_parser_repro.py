import subprocess
import pytest
import os

PARSER_BIN = "./lib/yaml/_yaml_parser"

def run_parser(input_str):
    if not os.path.exists(PARSER_BIN):
        # Try to build it? No, assume environment is prepared or specific tool usage
        pytest.fail(f"Parser binary not found at {PARSER_BIN}")
    
    proc = subprocess.Popen(
        [PARSER_BIN],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = proc.communicate(input=input_str)
    return proc.returncode, stdout, stderr

@pytest.mark.parametrize("name, yaml_str, expected_success", [
    ("basic_map", "key: val\n", True),
    ("anchor_doc", "&A\nkey: val\n", True),
    ("tag_doc", "!tag\nkey: val\n", True),
    ("tag_flow_map", "!tag { key: val }\n", True),
    ("repro_minimal", "!tag {}: val\n", True),
    ("repro_countdown", "&countdown\n!xargs { test, 0, -eq }: Liftoff!\n", True),
    ("repro_countdown_full", "&countdown\n!xargs {}: Liftoff!\n!xargs {}: !seq\n", True),
    ("repro_multiline", "A: 1\nB: 2\n", True),
    ("repro_anchor_multiline", "&A\nA: 1\nB: 2\n", True),
    ("repro_nested_anchor", "&A\n&B Key: Val\n", True),
    ("repro_tag_anchor", "!tag &A Key: Val\n", True),
    ("repro_anchor_tag", "&A !tag Key: Val\n", True),
])
def test_parser_cases(name, yaml_str, expected_success):
    ret, out, err = run_parser(yaml_str)
    if expected_success and ret != 0:
        pytest.fail(f"Parser failed for {name} (Exit {ret}).\nError: {err}\nOutput: {out}")
    if not expected_success and ret == 0:
        pytest.fail(f"Parser succeeded for {name} but expected failure.\nOutput: {out}")

if __name__ == "__main__":
    # Allow running directly script for debug
    for name, s, exp in test_parser_cases.pytestmark[0].args[1]:
        print(f"Running {name}...")
        ret, out, err = run_parser(s)
        if (ret == 0) == exp:
            print("PASS")
        else:
            print(f"FAIL. Ret={ret}\nErr={err}")
