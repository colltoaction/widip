Widip
-----

> _Types? Where we're going, we don't need types!_

Widip is an [interactive environment] for computing in modern systems. Many long-standing systems have thrived thanks to a uniform metaphor, which in our case is wiring diagrams.

System   |Metaphor
---------|--------------
Widip    |Wiring Diagram
UNIX     |File
Lisp     |List
Smalltalk|Object

![](examples/typical-vscode-setup.png)


# Installation

`widip` can be installed via [pip](https://pypi.org/project/widip/) and run from the command line as follows:

```bash
pip install widip
python -m widip
```

This will automatically install dependencies: [discopy](https://pypi.org/project/discopy/) (computing, drawing), [pyyaml](https://pypi.org/project/pyyaml/) (parser library), and [watchdog](https://pypi.org/project/watchdog/) (filesystem watcher).

## Local install

If you're working with a local copy of this repository, run `pip install -e .`.

# Using `widip`
The `widip` program starts a [chatbot] or [command-line interface]. It integrates with the [filesystem] for rendering diagram files. We give more information for a few use cases below.

## For documentation
Widis are meant for humans before computers and we find it valuable to give immediate visual feedback. Changes in a `.yaml` file trigger rendering a `.jpg` file next to it. This guides the user exploration while they can bring their own tools. As an example, VS Code will automatically reload markdown previews when `.jpg` files change.

Widis are great for communication and this is a very convenient workflow for git- and text-based documentation.

## For UNIX programming
The lightweight `widish` [UNIX shell] works everywhere from developer workstations to cloud environments to production servers. Processes that read and write YAML document streams are first-class citizens. With this practical approach users can write programs in the same language of widis.

## For graphical programming
Programming is hard, but it shouldn't be _that_ hard.

So far widis have mainly shaped the user interface. Widis are also [graphical programming](https://graphicallinearalgebra.net/2015/04/26/adding-part-1-and-mr-fibonacci/) tools and one can work with them in purely mathematical terms. Start with [examples/mascarpone](examples/mascarpone) then take a look at current work in a functional library at [src](src).


[UNIX shell]: https://en.wikipedia.org/wiki/Unix_shell
[chatbot]: https://en.wikipedia.org/wiki/chatbot
[command-line interface]: https://en.wikipedia.org/wiki/Command-line_interface
[filesystem]: https://en.wikipedia.org/wiki/File_manager
[interactive environment]: https://en.wikipedia.org/wiki/Read%E2%80%93eval%E2%80%93print_loop
