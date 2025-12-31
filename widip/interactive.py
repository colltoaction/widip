import asyncio
import sys
from pathlib import Path
from yaml import YAMLError

from discopy.utils import tuplify

from .files import file_diagram, repl_read
from .widish import SHELL_RUNNER
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
    runner = SHELL_RUNNER(compiled_d)(*constants)

    if sys.stdin.isatty():
        inp = ""
    else:
        inp = await loop.run_in_executor(None, sys.stdin.read)
        
    run_res = runner(inp)
    val = await unwrap(run_res)
    print(*(tuple(x.rstrip() for x in tuplify(val) if x)), sep="\n")


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
            result_ev = SHELL_RUNNER(compiled_d)(*constants)
            result = await unwrap(result_ev)
            print(*(tuple(x.rstrip() for x in tuplify(result) if x)), sep="\n")

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
