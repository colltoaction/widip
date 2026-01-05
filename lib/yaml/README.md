# C YAML Parser

This implementation uses standard compiler tools (Lex and Yacc) to parse YAML.

Current Status: 155 tests passing and 196 failing.

## Usage

You can build and run the parser using the terminal:

```bash
lex yaml.l                       # Generate lexer (lex.yy.c)
yacc -d yaml.y                   # Generate parser (y.tab.c, y.tab.h)
cc lex.yy.c y.tab.c -lfl -o yaml # Compile
./yaml < input.yaml              # Run
```

## Design

We employ a standard LALR(1) grammar, similar to those defining languages like C or Python. To accommodate YAML's significant indentation, the lexer pre-processes whitespace into explicit tokens. This approach allows us to use mathematically well-understood tools (`flex` and `bison`) rather than ad-hoc parsing strategies.

### References

- [The YAML Specification (1.2.2)](https://yaml.org/spec/1.2.2/)
- `man 1 bison`, `man 1 flex`
