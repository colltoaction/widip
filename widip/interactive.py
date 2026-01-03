import asyncio
import sys
from pathlib import Path
from yaml import YAMLError
from typing import IO
from io import StringIO

from discopy.utils import tuplify

from .files import file_diagram, repl_read
from .exec import EXEC as SHELL_RUNNER, flatten
from .widish import Process
from .thunk import unwrap
from .compiler import SHELL_COMPILER
from .computer import Language


def prepare_input_stream(args: list[str], stdin_content: str) -> IO[str]:
    combined_input_str = "\n".join(args)
    if stdin_content:
        if combined_input_str: combined_input_str += "\n"
        combined_input_str += stdin_content
    return StringIO(combined_input_str)


async def async_exec_diagram(yaml_d, path, *shell_program_args):
    loop = asyncio.get_running_loop()
    
    # Debug drawing logic
    if __debug__ and path is not None:
        from .files import diagram_draw
        diagram_draw(path, yaml_d)

    compiled_d = SHELL_COMPILER(yaml_d)
    
    if __debug__ and path is not None:
        from .files import diagram_draw
        diagram_draw(path.with_suffix(".shell.yaml"), compiled_d)
    
    runner_process = SHELL_RUNNER(compiled_d)
    
    # Read stdin if available (buffered approach is simpler and less intrusive)
    stdin_content = ""
    if not sys.stdin.isatty():
        stdin_content = await loop.run_in_executor(None, sys.stdin.read)
    
    input_stream = prepare_input_stream(list(shell_program_args) if shell_program_args else [], stdin_content)
    
    inp = (input_stream,)
    if not runner_process.dom:
         inp = ()

         
    # Execute
    if inp:
        res = await unwrap(runner_process(*inp))
    else:
        res = await unwrap(runner_process())
    
    # Output handling
    filtered = await flatten(res)
    if filtered:
        print(*filtered, sep="\n", flush=True)


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
