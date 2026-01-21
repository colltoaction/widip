# Execution Model

In `widip`, YAML tags such as `!eval`, `!read`, or `!print` are interpreted as **commands to execute**.

## Using Executables

You can use **any executable** that exists in your system's `$PATH` or by providing a relative/absolute path.

**Examples:**

*   **System tools:** `!python`, `!grep`, `!awk`.
*   **Custom scripts:** `!./myscript.sh`.

## Using Other YAML Files

You can also use other `widip` YAML files as commands, provided they are executable (e.g., they have a valid shebang like `#!bin/widish`). This allows you to compose complex pipelines from smaller, reusable diagrams.

**Example:**

```yaml
- !executable.yaml
```

This will execute the `executable.yaml` diagram as a step in your current pipeline.
