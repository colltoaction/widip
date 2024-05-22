# Wiring Diagram Processing
Widip is a graphical shell for UNIX with an interactive prompt.

## Quickstart

```
$ git clone https://github.com/colltoaction/widip.git
$ cd widip
$ pip install yaml discopy watchdog
$ python . examples/hello-world.yaml
Hello world!
$ open examples/hello-world.jpg
```

![](examples/hello-world.jpg)

## Documentation
You will find the documentation alongside the wiring diagram text and visual representations. You are encouraged to explore and interact with the whole filesystem.

## Introduction

### Why Graphical Programming

Programming is a hard reasoning task helped with widis. Just like text flowing from top to bottom, widis have the same orientation that is natural for programming languages.

### Why YAML

YAML is a widely-adopted human-friendly language for describing object relations. We leverage several features to create an elegant textual representation of arbitrary widis.

### Why UNIX

UNIX is a key piece in the computing world. This environment is standard from developer workstations to production servers. We use it to create a productive developer experience and server workloads with minimal dependencies.

## Environment
### Setup
A typical setup looks like:

1. Open VS Code
2. Open terminal and run `python .` to start an interactive session
3. While running, `.jpg`s will be synced on file changes
4. Open `.yaml` and `.jpg` files side by side for a fast feedback loop
5. Use the shell to interact with the system

In step 2 Python starts an interactive session with the program `bin/yaml/shell.yaml` and you see a prompt just like in Bash or Python. `↵ Enter` evaluates the line and `⌁ Ctrl+D` exits.

```
$ python .
--- !bin/yaml/shell.yaml
!!python/eval 40+2
42
--- !bin/yaml/shell.yaml
⌁
```

### Displaying widis
As seen above, `.yaml` files are evaluated by the Widip shell and produce `.jpg`s. Each and every YAML document has an interpretation as a widi. The generated images are committed for an effective built-in documentation.

### Widi programs
Widis are [graphical programming](https://graphicallinearalgebra.net/2015/04/26/adding-part-1-and-mr-fibonacci/) tools that have two main operations: parallel and sequential composition. As a formal method they have excellent properties to connect open systems like programs.

To program with widis we build a functional library written in Widip itself. As an example core abstractions like `bool` or `maybe` can be found in the [](src/data) directory.

The shell processes wiring diagrams by replacing boxes until it is left just with primitive operations. Building such a language leads to a self-contained fully-dynamic system.

## Inspiration

* UNIX: pipelines, everything is a file
* LISP: code as data
* Clojure: everything LISP + extended syntax
* Idris: dependently-typed implementations
