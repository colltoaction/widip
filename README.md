# YAML Diagrams

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

## Introduction

Diagrams are [graphical programming](https://graphicallinearalgebra.net/2015/04/26/adding-part-1-and-mr-fibonacci/) tools that have two main operations: parallel and sequential composition. As a formal method they have excellent properties to connect open systems like programs.

We implement a Diagram development environment with a [YAML](https://yaml.org) DSL and file and directory integration. At the same time we work on a functional programming language written with Diagrams, which feeds back into the DSL design. Core abstractions like `bool` or `maybe` can be found in the `src/data` directory.

> For an academic introduction check this paper:
> * https://github.com/colltoaction/qpl2024/blob/main/YAML%20Diagrams/YAML%20Diagrams.pdf


## Why YAML

My intuition came from the observation that I was writing the same code time and time again.
Not every language supports the same functional patterns and common tasks turn repetitive and error prone.

YAML is a human-friendly language and is suited for describing object relations, including graphs, syntax trees, functions and more. We define and publish common functional abstractions that can be implemented in any language.

These are inpiration:
* Haskell: do notation
* Scala: for comprehensions, cats
* Smalltalk: method call syntax
* LISP: code as data
* UNIX: pipelining

## Development environment

The developer experience (DX) is designed with minimal dependencies in mind. A typical setup looks like this:

1. Open VS Code
2. Open terminal and run `python .` to start an interactive session with the YAML Diagrams shell
3. While running the shell will autoreload any changes in the directory
4. Open `.yaml` and `.jpg` files side by side for a fast feedback loop
5. Use the shell to interact with the system

The shell prompt `--- !bin/yaml/shell.yaml` indicates it is ready to receive a YAML document and process it with the specified file. `↵ Enter` evaluates the line and `⌁ Ctrl+D` exits.

```sh
$ python .↵
--- !bin/yaml/shell.yaml
!!python/eval 40+2
42
--- !bin/yaml/shell.yaml
⌁
```

## Operating system

This tool has important considerations for the development environment:
* UNIX: follows philosophy and is deeply integrated
* Smalltalk: follows design principles

Even when using UNIX, we want to follow Smalltalk design principles as well.

Code editing:
* support in all OSs
* wide variety of features in YAML
* unified sdlc language
