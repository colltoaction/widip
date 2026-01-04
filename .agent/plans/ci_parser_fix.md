# Plan: CI Updates, Parser Binary Renaming, and Test Fixes

## 1. CI Workflow Update
- Update `.github/workflows/ci.yml` to include `pip install .[test]` step after system dependencies.

## 2. Rename Generated Parser Binary
- Rename the generated binary from `yaml_parser` to `_yaml_parser` to clearly indicate it is an internal/generated file.
- Update `Makefile` to output `_yaml_parser`.
- Update `.gitignore` to ignore `_yaml_parser`.
- Update `lib/computer/parser_bridge.py` to look for `_yaml_parser`.

## 3. Fix Test Failures
- **`tests/test_compilation.py`**:
    - `test_compilation.py` fails with `IndexError`. This is likely because the parser now returns a `Sequence` (list of boxes) for the root `stream`, but the test expects a single box or a specific structure.
    - I need to inspect how `root = make_seq($1)` in `yaml.y` affects the output structure in `parser_bridge.py`.
    - If `parser_bridge.py` wraps everything in a `Sequence`, `load()` might return a Diagram whose first box is that Sequence, or it might be trying to interpret it directly.
    - Debug `load()` output for simple cases.

- **`tests/test_anchors.py` & `test_logic.py`**:
    - `ValueError: Unknown anchor: *v`.
    - `Unknown node type - return identity on Node` handling in `parser_bridge.py` might be missing `ANCHOR` handling if my previous edit to `parser_bridge.py` was incomplete or incorrect. I added `TAG` support. I need to verify `ANCHOR` support in `parser_bridge.py`.
    - Also, `tests/test_logic.py` failure `ValueError: Unknown anchor: *v` happens at runtime (or load time?). If it's `ValueError`, it might be raised by `construct.py` or `parser_bridge.py`.

## 4. Parser Checks
- Verify `yaml.y` constructs `NODE_ANCHOR` correctly (it seems to).
- Verify `parser_bridge.py` handles `ANCHOR` and `ALIAS` correctly.

## 5. Execution
- Run `make rebuild-parser` after renaming.
- Run tests (`make test`).
