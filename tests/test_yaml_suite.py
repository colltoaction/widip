
import pytest
import os
import glob
from pathlib import Path
from computer.yaml import load

# Path to the YAML Test Suite 'src' directory
# Assuming tests/yaml-test-suite is rooted at the project root
TEST_SUITE_SRC = Path(__file__).parent / "yaml-test-suite" / "src"

def get_test_cases():
    """
    Yields test cases from the YAML Test Suite.
    Each case is a tuple: (test_id, description, yaml_content)
    """
    if not TEST_SUITE_SRC.exists():
        return
        
    for yaml_file in glob.glob(str(TEST_SUITE_SRC / "*.yaml")):
        try:
            # We parse the test suite definition file manually or with PyYAML if needed
            # But wait, the test suite files themselves are YAML.
            # They contain input YAML for the test in the 'yaml' field.
            # We need a reliable way to extract that 'yaml' field WITHOUT using our own parser
            # if our parser is what we are testing (and it might be broken).
            # However, for now, let's try to use a simple text extraction or a reliable library 
            # if we can install one, or just simple string splitting if the format is consistent.
            
            # The format is:
            # ---
            # - name: ...
            #   yaml: |
            #     <content>
            
            # This is hard to parse robustly without a parser.
            # Let's hope basic parsing works or install PyYAML for the test runner.
            # The system has python 3.10+, likely has PyYAML or we can rely on our `computer.yaml` 
            # if we trust it enough for the metadata. PROBABLY NOT.
            
            # Strategy: Simply read the file and look for "yaml: |"
            with open(yaml_file, 'r') as f:
                content = f.read()
            
            if "yaml: |" in content:
                # Naive extraction
                parts = content.split("yaml: |")
                if len(parts) > 1:
                    # The content is indented.
                    raw_yaml_block = parts[1].split("\n")
                    # First line is empty (after |)
                    # We need to detect indentation of the first non-empty line
                    yaml_lines = []
                    indent = None
                    for line in raw_yaml_block[1:]: # Skip first newline after pipe
                        if not line.strip(): 
                            yaml_lines.append("")
                            continue
                        
                        current_indent = len(line) - len(line.lstrip())
                        if indent is None:
                            indent = current_indent
                        
                        if current_indent < indent:
                            # End of block
                            break
                        
                        yaml_lines.append(line[indent:])
                    
                    yaml_content = "\n".join(yaml_lines)
                    test_id = Path(yaml_file).stem
                    yield test_id, yaml_content
        except Exception:
            continue

@pytest.mark.parametrize("test_id, yaml_content", get_test_cases())
def test_yaml_suite(test_id, yaml_content):
    """Run a test case from the YAML Test Suite."""
    try:
        # We only check if it executes/parses without crashing for now.
        # Validating output structure against the suite's 'json' or 'tree' is harder 
        # because our AST structure is custom (DisCoPy diagrams).
        
        diag = load(yaml_content)
        assert diag is not None
        
    except Exception as e:
        pytest.fail(f"Failed to parse/load test {test_id}: {e}")
