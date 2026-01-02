import asyncio
import sys
from pathlib import Path
from yaml import YAMLError

from discopy.utils import tuplify

from .files import file_diagram, repl_read
from .widish import SHELL_RUNNER, Process, fold_diagram
from .thunk import unwrap
from .compiler import SHELL_COMPILER


async def async_exec_diagram(yaml_d, path, *shell_program_args):
    loop = asyncio.get_running_loop()

    if __debug__ and path is not None:
        from .files import diagram_draw
        diagram_draw(path, yaml_d)

    constants = tuple(x.name for x in yaml_d.dom)
    compiled_d = SHELL_COMPILER(yaml_d)

    if __debug__ and path is not None:
        from .files import diagram_draw
        diagram_draw(path.with_suffix(".shell.yaml"), compiled_d)
    
    compiled_widish = SHELL_RUNNER(compiled_d)
    runner_process = fold_diagram(compiled_widish)
    
    # Map shell_program_args to the initial input
    # If the diagram expects input, use shell_program_args or stdin
    initial_input = shell_program_args if shell_program_args else []
    
    if sys.stdin.isatty():
        inp = initial_input
    else:
        stdin_data = await loop.run_in_executor(None, sys.stdin.read)
        inp = list(initial_input) + (stdin_data.splitlines() if stdin_data else [])

    # Force at least empty string if input is empty, to prevent pipeline abortion on empty stream
    if not inp:
        inp = [""]

    # Execute the folded process with the input
    if runner_process.dom:
        res = await unwrap(runner_process(*tuplify(inp)))
    else:
        res = await unwrap(runner_process())
    
    if res != ():
        to_print = tuplify(res)
        if not (len(to_print) == 1 and to_print[0] is None):
             print(*(x for x in to_print if x is not None), sep="\n")


async def async_command_main(command_string, *shell_program_args):
    fd = repl_read(command_string)
    # No file path associated with command string
    await async_exec_diagram(fd, None, *shell_program_args)


async def async_widish_main(file_name, *shell_program_args):
    fd = file_diagram(file_name)
    path = Path(file_name)
    await async_exec_diagram(fd, path, *shell_program_args)


async def async_shell_main(file_name):
    path = Path(file_name)
    loop = asyncio.get_running_loop()

    while True:
        try:
            if not sys.stdin.isatty():
                source = await loop.run_in_executor(None, sys.stdin.read)
                if not source:
                    break
            else:
                prompt = f"--- !{file_name}\n"
                source = await loop.run_in_executor(None, input, prompt)

            yaml_d = repl_read(source)
            if __debug__:
                from .files import diagram_draw
                diagram_draw(path, yaml_d)
            source_d = SHELL_COMPILER(yaml_d)
            compiled_d = source_d
            # compiled_d = SHELL_COMPILER(source_d)
            # if __debug__:
            #     diagram_draw(path.with_suffix(".shell.yaml"), compiled_d)
            constants = tuple(x.name for x in compiled_d.dom)
            result = await unwrap(SHELL_RUNNER(compiled_d)(*constants))
            print(*(tuplify(result)), sep="\n")

            if not sys.stdin.isatty():
                break
        except EOFError:
            if sys.stdin.isatty():
                print("⌁", file=sys.stderr)
            break
        except KeyboardInterrupt:
            print(file=sys.stderr)
        except YAMLError as e:
            print(e, file=sys.stderr)
