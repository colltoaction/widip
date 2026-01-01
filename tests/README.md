# Widish Tests

This directory contains test cases for the `widish` shell environment. `widish` combines the familiarity of shell commands with the structure and composability of YAML.

## What is Widish?

`widish` allows you to write shell scripts as YAML documents. Data flows through the structure, enabling:

-   **Structured Pipelines**: Use YAML sequences (lists) to pipe data between commands.
-   **Structured Data**: Pass structured data (like YAML mappings) between processes, not just text streams.
-   **Composition**: Reuse YAML files as scripts/commands within other YAML scripts.
-   **Implicit Parallelism**: Use mappings to branch data flow to multiple commands simultaneously.

## Running Tests

Tests are run using `pytest` and the `tests/test_harness.py` script. The harness executes each `.test.yaml` file using `bin/widish` and compares the standard output to the corresponding `.log` file.

```bash
pytest tests/test_harness.py
```

## Test Case Format

Each test case consists of two files:

1.  `tests/CASE.test.yaml`: The input YAML script.
2.  `tests/CASE.log`: The expected standard output.

### Example: Infinite Counter

This example demonstrates using an infinite generator (`yes`), processing it, and limiting the output (`head`). It relies on `bin/yaml/range.yaml` which defines the infinite stream.

`tests/infinite-counter.test.yaml`:
```yaml
- !bin/yaml/range.yaml
- !head -n 5
```

`tests/infinite-counter.log`:
```
1
2
3
4
5
```
