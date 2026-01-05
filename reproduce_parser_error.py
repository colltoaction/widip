import subprocess
import os

def test_parser(source):
    parser_path = "lib/yaml/_yaml_parser"
    if not os.path.exists(parser_path):
        print(f"Parser not found at {parser_path}")
        return
    
    print(f"--- Testing source ---\n{source}\n----------------------")
    process = subprocess.run(
        [parser_path],
        input=source.encode(),
        capture_output=True
    )
    
    if process.returncode != 0:
        print(f"ERROR (exit {process.returncode}):")
        print(process.stderr.decode())
    else:
        print("SUCCESS:")
        print(process.stdout.decode())

if __name__ == "__main__":
    # Test case 1: simple mapping
    test_parser("key: value")
    
    # Test case 2: mapping with indented sequence (fails in tests)
    test_parser("key:\n  - item")
    
    # Test case 3: mapping with indented mapping
    test_parser("outer:\n  inner: value")

    # Test case 5: anchored mapping
    test_parser("&countdown\nkey: value")

    # Test case 6: tagged mapping key with flow mapping
    test_parser("!xargs { a, b }: value")

    # Test case 7: combined
    test_parser("&countdown\n!xargs { test, 0, -eq }: Liftoff!\n!xargs { test, 0, -lt }: !seq\n  - !print")

    # Test case 8: tagged indented sequence
    test_parser("key: !seq\n  - item")
    # Test case 10: basic multi-entry mapping
    test_parser("a: b\nc: d")

    # Test case 11: mapping with scalar then mapped sequence
    test_parser("a: b\nc: !seq\n  - d")

    # Test case 12: sequential complex keys
    test_parser("!tag { a }: b\n!tag { c }: d")

    # Test case 13: tagged scalar keys
    test_parser("!tag a: b\n!tag c: d")

    # Test case 14: complex keys with ?
    test_parser("? !tag a: b\n? !tag c: d")

    # Test case 9: combined without anchor
    test_parser("!xargs { test, 0, -eq }: \"Liftoff!\"\n!xargs { test, 0, -lt }: !seq\n  - !print")

    # Test case 9: combined without anchor
    test_parser("!xargs { test, 0, -eq }: \"Liftoff!\"\n!xargs { test, 0, -lt }: !seq\n  - !print")

    # Test case 9: combined without anchor
    test_parser("!xargs { test, 0, -eq }: \"Liftoff!\"\n!xargs { test, 0, -lt }: !seq\n  - !print")
