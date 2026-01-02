# Titi: Titi is Terminal Intelligence

**Titi bridges the gap between human intuition and machine precision.** It provides the structured communication and reasoning tools necessary for complex orchestration. By using **diagrams** as its core metaphor, Titi transforms the shell into a modern **interactive environment** built to run workflows for both humans and autonomous systems.

- **For Agents**: Titi leverages the YAML standard as a shared language for humans and agents. Instead of parsing messy text, agents reason using the same structured maps as humans, making their orchestration more predictable and reliable.
- **For End Users**: Titi transforms "black-box" agent behavior into a transparent "white-box" loop. Its real-time diagrammatic feedback allows anyone to visually audit and understand an agent's reasoning as it unfolds.


## Getting Started

By leveraging the simplicity of YAML, the Titi Shell feels instantly familiar. It is designed for anyone who needs high-precision orchestration—honestly, for everyone. Install it via [pip](https://pypi.org/project/titi-sh/) and enter the environment instantly:

```bash
# 1. Install the shell for agents
pip install titi-sh

# 2. Enter the Titi Shell (the --watch flag enables live diagram updates)
titi --watch
```

## Quick Demo

The following demo showcases **Titi Shell** running with the **`--watch`** flag:
1. **Live Feedback**: Notice the "watching for changes" message on startup.
2. **Implicit Pipelines**: Running `!ls src: !wc -l` to count source directories.
3. **Stateful Recursion**: Executing [`examples/demo.yaml`](examples/demo.yaml) to calculate a factorial (5! = 120) using diagrammatic recursion.

<img src="examples/demo.svg" width="600">

### Inside [`examples/demo.yaml`](examples/demo.yaml)
A linear pipeline demonstrating sequential composition without complexity:
```yaml
!seq
- !echo "Welcome to Titi Shell"
- !tee /dev/stderr
- !tr "[:lower:]" "[:upper:]": !tr "[:upper:]" "[:lower:]"
- !cat
```

This composition demonstrates sequential processing and parallel execution (forking to two transformers).

> Dependencies include [discopy](https://pypi.org/project/discopy/), [watchfiles](https://pypi.org/project/watchfiles/), and [nx-yaml](https://pypi.org/project/nx-yaml/).


## The Titi Shell

**You are in the driver's seat.** Titi helps you design, visualize, and control complex systems with ease. Whether you're debugging a simple pipeline or orchestrating a heavy workload, Titi keeps you in flow and in control.


## For Transparent Reasoning
Diagrams aren't just for humans; they are the high-level maps agents use to navigate complexity. When run with the **`--watch`** flag, Titi provides immediate visual feedback: as you and the agents work together in a codebase, Titi automatically re-renders the corresponding `.jpg` diagrams.

This enables a seamless loop for human-in-the-loop oversight:
1. Run `titi --watch` to enable visual orchestration.
2. Agents propose or modify a workflow in YAML.
3. Titi updates the visual diagram in real-time.
4. Use VS Code's **Markdown Preview** (`Ctrl+Shift+V`) to audit the agent's logic visually as it evolves.

## For the Human Oversight
Titi is not just for agents; it is for the humans who build, audit, and coordinate them. By providing a common diagrammatic language, Titi empowers users with:
- **Visual Auditing**: Instantly see how an agent is wiring together system tools.
- **Rapid Composition**: Wire up complex shell pipelines in YAML and hand them to an agent as a single, high-level capability.
- **Cross-Layer Observability**: Move seamlessly between raw terminal output and structured visual maps to debug complex agentic multi-step plans.

## The Agent's Choice
We believe programming should be as intuitive for agents as it is for humans. Titi is built for [agentic programming], where agents interact with system tools through simple diagram interfaces. By turning low-level shell details into composable diagrams, Titi allows agents to plan and execute complex tasks with much better clarity—while giving humans the visibility they need to stay in control.

## Computing Metaphors

Every major shift in computing has been driven by a new unifying metaphor. Just as **UNIX** unified system resources around the **File**, **Lisp** around the **List**, and **Smalltalk** around the **Object**, Titi unifies system orchestration around the **Diagram**.

System   |Metaphor
---------|--------------
**Titi** |**Diagram**
UNIX     |File
Lisp     |List
Smalltalk|Object

This shift elevates the shell from a text processor to a visual orchestration engine, making complex state and concurrency as intuitive to manipulate as files.

[UNIX shell]: https://en.wikipedia.org/wiki/Unix_shell
[agentic programming]: https://en.wikipedia.org/wiki/Autonomous_agent
[chatbot]: https://en.wikipedia.org/wiki/chatbot
[command-line interface]: https://en.wikipedia.org/wiki/Command-line_interface
[filesystem]: https://en.wikipedia.org/wiki/File_manager
[interactive environment]: https://en.wikipedia.org/wiki/Read%E2%80%93eval%E2%80%93print_loop

## Local Development

For development, clone the repository and run:
```bash
pip install -e .[test]
```
