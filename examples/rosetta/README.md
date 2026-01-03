# Rosetta Code Examples

Examples from [rosettacode.org](https://rosettacode.org) implemented in widip.

## FizzBuzz

Classic FizzBuzz using standard Unix tools (`xargs`, `printf`, `bc`, `test`, `tee`).

```bash
python -m widip examples/rosetta/FizzBuzz.yaml | head -16
# Expected:
# 1
# 2
# Fizz
# 4
# Buzz
# Fizz
# 7
# 8
# Fizz
# Buzz
# 11
# Fizz
# 13
# 14
# FizzBuzz
# 16
```

<img src="FizzBuzz.shell.svg" width="600">

## Fibonacci

Recursive Fibonacci structure demonstration.

<img src="fibonacci.svg" width="400">

## Repeat a String

Simple string repetition using Python eval.

```bash
echo "ha" | python -m widip examples/rosetta/repeat-a-string.yaml
# Expected: hahahahaha
```
