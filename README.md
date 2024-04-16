# YAML Diagrams
Graphical programming with YAML on UNIX.

## Quickstart

```sh
$ git clone https://github.com/yaml-programming/diagrams.git
$ cd diagrams
$ pip install yaml discopy watchdog
$ python . examples/hello-world.yaml
Hello world!
$ open examples/hello-world.jpg
```

![](examples/hello-world.jpg)

You will find the rest of the documentation in the `README.md` files in this repository. Readme files take advantage of generated `.jpg`s for an effective built-in documentation.

## Introduction

### Why Graphical Programming

Programming is a hard reasoning task helped with Diagrams, a data structure in the sense of Abstract Syntax Trees or Graphs. Just like text flowing from top to bottom, Diagrams have the same orientation that is natural for programming languages.

### Why YAML

YAML is a widely-adopted human-friendly language for describing object relations. We leverage several features to create an elegant textual representation of Diagrams. This tradeoff gives users the chance to decouple syntax from semantics.

### Why UNIX

UNIX is a key piece in the computing world. This environment is standard from developer workstations to production servers. We use it to create a productive developer experience and server workloads with minimal dependencies.

## Shell

As programming tools and languages, existing shells collide with this project's goals. The REPL and Shell distinction is dropped and we encourage users to use a single-language approach. A typical setup looks like:

1. Open VS Code
2. Open terminal and run `python .` to start an interactive session
3. While running, `.jpg`s will be synced on file changes
4. Open `.yaml` and `.jpg` files side by side for a fast feedback loop
5. Use the shell to interact with the system

In step 2 Python starts an interactive session with the program `bin/yaml/shell.yaml` and you see a prompt just like in Bash or Python. `↵ Enter` evaluates the line and `⌁ Ctrl+D` exits.

```sh
$ python .
--- !bin/yaml/shell.yaml
!!python/eval 40+2
42
--- !bin/yaml/shell.yaml
⌁
```

## Operating system

We implement a Diagram development environment with a [YAML](https://yaml.org) DSL and file and directory integration. At the same time we work on a functional programming language written with Diagrams, which feeds back into the DSL design. Core abstractions like `bool` or `maybe` can be found in the `src/data` directory.

Diagrams are [graphical programming](https://graphicallinearalgebra.net/2015/04/26/adding-part-1-and-mr-fibonacci/) tools that have two main operations: parallel and sequential composition. As a formal method they have excellent properties to connect open systems like programs.

## Inspiration

* UNIX: pipelines, everything is a file
* LISP: code as data
* Clojure: everything LISP + extended syntax
* Idris: dependently-typed implementations
