# YAML Diagrams

## Quickstart

```sh
$ git clone https://github.com/yaml-programming/diagrams.git
$ cd diagrams
$ pip install yaml discopy
$ python . examples/hello-world.yaml
Hello world!
$ open examples/hello-world.gif
```

![](examples/hello-world.gif)

## Introduction

Diagrams are [graphical programming](https://graphicallinearalgebra.net/2015/04/26/adding-part-1-and-mr-fibonacci/) tools that have two main operations: parallel and sequential composition. As a formal method they have excellent properties to connect open systems like programs.

We implement a Diagram development environment with a [YAML](https://yaml.org) DSL and file and directory integration. At the same time we work on a functional programming language written with Diagrams, which feeds back into the DSL design. Core abstractions like `bool` or `maybe` can be found in the `src/yaml/data` directory.

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
> Note: Expertise with `make`, `bash` or UNIX in general isn't required to write diagrams.

### Setup
Just cloning the repository and running `make` will show there are no changes to be made.
Every commit is guaranteed to be idempotent on the `make` invocation to make things straightforward.

### Dev loop
Whenever you change the `src/yaml` contents, running `make` will validate only the changed files. On success these are compiled and outputted as gifs next to the `.yaml` file.
Every directory is also scanned and a string diagram gif describing its contents is automatically generated.

## Operating system

This tool has important considerations for the development environment:
* UNIX: follows philosophy and is deeply integrated
* Smalltalk: follows design principles

Even when using UNIX, we want to follow Smalltalk design principles as well.

Code editing:
* support in all OSs
* wide variety of features in YAML
* unified sdlc language
