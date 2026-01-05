# C YAML Parser

This directory contains a C-based Lex/Yacc YAML parser designed for bootstrapping the Monoidal Computer.

## Architecture

- `yaml.l`: Flex lexer definition. Handles indentation through a start-condition stack and token queuing (INDENT/DEDENT).
- `yaml.y`: Bison/Yacc grammar. Implements a flexible subset of YAML 1.2, focusing on block and flow styles, anchors, and tags.
- `parser_bridge.py` (in `lib/computer/yaml/`): Python interface that calls the compiled binary and reconstructs the AST.

## Features

- **Indentation Aware**: Uses a custom lexer state machine to generate INDENT and DEDENT tokens.
- **Recursive Properties**: Supports complex combinations of anchors and tags (e.g., `&anchor !tag node`).
- **Flow & Block Interoperability**: Correctly handles flow nodes within block sequences and mappings.
- **Fast**: High-performance parsing compared to pure Python implementations.
- **Compliant**: Aiming for 100% compliance with the YAML test suite.

## Usage

The parser is typically built via the top-level `Makefile`:

```bash
make parser  # Builds the binary bin/yaml/parse
```

The binary `bin/yaml/parse` reads from stdin and outputs a debug representation of the AST.
