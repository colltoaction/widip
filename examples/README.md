# Shell examples

## Hello world!

```
$ ./examples/hello-world.yaml
Hello world!
```

![](hello-world.jpg)

![](hello-world.shell.jpg)

## Script

```
$ ./examples/shell.yaml
73
23
  ? !grep { grep: }: !wc { -c }
  ? !tail { -2 }
```

![IMG](shell.jpg)

![IMG](shell.shell.jpg)

## Countdown
Recursive countdown orchestration. It uses `test` for termination, `expr` for arithmetic, and a built-in feedback trace in the `widish` runtime to print values during recursion.

```
$ examples/countdown.yaml
3
2
1
Liftoff!
```

![IMG](countdown.jpg)

![IMG](countdown.shell.jpg)

# Working with the CLI
Open terminal and run `widip` to start an interactive session. The program `bin/yaml/shell.yaml` prompts for one command per line, so when we hit `↵ Enter` it is evaluated. When hitting `⌁ Ctrl+D` the environment exits.

```yaml
--- !bin/yaml/shell.yaml
!echo Hello world!
Hello world!
```

# Other examples

## React
The first example in https://react.dev/ in diagrammatic style.

![](react.jpg)

## Sweet expressions
`fibfast` function from https://wiki.c2.com/?SweetExpressions.

![](sweet-expressions.jpg)

## Rosetta code

* https://rosettacode.org
* [rosetta](rosetta) examples directory
